import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import create_app
from app.api import dependencies as di
from app.services.index_service import IndexService
from app.repositories.memory.library_repository import InMemoryLibraryRepository
from app.repositories.memory.document_repository import InMemoryDocumentRepository
from app.repositories.memory.chunk_repository import InMemoryChunkRepository


class FakeEmbedding:
    def embed(self, text: str, input_type: str = "search_document", dimension: int = 32):
        # Deterministic simple embedding to avoid external calls
        base = sum(ord(c) for c in text) % 100
        return [(base + i) * 0.01 for i in range(dimension)]


@pytest.fixture
def client():
    app = create_app()

    # Fresh in-memory singletons per test
    library_repo = InMemoryLibraryRepository()
    document_repo = InMemoryDocumentRepository()
    chunk_repo = InMemoryChunkRepository()
    embedding = FakeEmbedding()
    index_service = IndexService(chunk_repo, embedding)

    # Rebuild services graph mirroring app.api.dependencies
    from app.services.chunk_service import ChunkService
    from app.services.document_service import DocumentService
    from app.services.library_service import LibraryService

    chunk_service = ChunkService(
        chunk_repository=chunk_repo,
        library_repository=library_repo,
        document_repository=document_repo,
        index_service=index_service,
        embedding_service=embedding,
    )
    document_service = DocumentService(
        library_repository=library_repo,
        document_repository=document_repo,
        chunk_service=chunk_service,
    )
    library_service = LibraryService(
        library_repository=library_repo,
        document_service=document_service,
        index_service=index_service,
    )

    # Override DI providers
    app.dependency_overrides[di.get_library_service] = lambda: library_service
    app.dependency_overrides[di.get_document_service] = lambda: document_service
    app.dependency_overrides[di.get_chunk_service] = lambda: chunk_service
    app.dependency_overrides[di.get_index_service] = lambda: index_service

    # Expose key services for introspection in tests
    app.state.index_service = index_service

    return TestClient(app)


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "healthy"


class TestLibraries:
    def test_create_library_success(self, client):
        r = client.post("/v1/libraries/", json={"name": "lib1", "index_type": "linear", "metadata": {}})
        assert r.status_code == 201
        body = r.json()
        assert body["name"] == "lib1"
        assert body["index_type"] == "linear"

    def test_create_library_missing_body(self, client):
        r = client.post("/v1/libraries/")
        assert r.status_code == 422

    def test_list_and_get_library(self, client):
        r = client.post("/v1/libraries/", json={"name": "lib2", "index_type": "linear"})
        lib_id = r.json()["id"]
        r = client.get("/v1/libraries/")
        assert r.status_code == 200
        assert lib_id in r.json()
        r = client.get(f"/v1/libraries/{lib_id}")
        assert r.status_code == 200
        assert r.json()["id"] == lib_id

    def test_get_library_not_found(self, client):
        r = client.get(f"/v1/libraries/{uuid4()}")
        assert r.status_code == 404

    def test_update_library_requires_some_field(self, client):
        lib = client.post("/v1/libraries/", json={"name": "lib3", "index_type": "linear"}).json()
        r = client.patch(f"/v1/libraries/{lib['id']}", json={})
        # Pydantic validator should yield 422
        assert r.status_code == 422

    def test_update_library_name_and_metadata(self, client):
        lib = client.post("/v1/libraries/", json={"name": "lib4", "index_type": "linear"}).json()
        r = client.patch(
            f"/v1/libraries/{lib['id']}", json={"name": "new", "metadata": {"a": 1}}
        )
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "new"
        assert body["metadata"] == {"a": 1}

    def test_delete_library_idempotent(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib5", "index_type": "linear"}).json()["id"]
        r1 = client.delete(f"/v1/libraries/{lib_id}")
        assert r1.status_code == 200
        r2 = client.delete(f"/v1/libraries/{lib_id}")
        # Service is idempotent; router returns 200 even if missing
        assert r2.status_code == 200


class TestDocuments:
    def setup_library(self, client):
        return client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]

    def test_create_document_success(self, client):
        lib_id = self.setup_library(client)
        r = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {"x": 1}})
        assert r.status_code == 201
        assert r.json()["library_id"] == lib_id

    def test_create_document_missing_body(self, client):
        lib_id = self.setup_library(client)
        r = client.post(f"/v1/libraries/{lib_id}/documents/")
        assert r.status_code == 422

    def test_get_document_not_found(self, client):
        lib_id = self.setup_library(client)
        r = client.get(f"/v1/libraries/{lib_id}/documents/{uuid4()}")
        assert r.status_code == 404

    def test_update_document_success(self, client):
        lib_id = self.setup_library(client)
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        r = client.patch(
            f"/v1/libraries/{lib_id}/documents/{doc['id']}", json={"metadata": {"a": 2}}
        )
        assert r.status_code == 200
        assert r.json()["metadata"] == {"a": 2}

    def test_update_document_missing_body(self, client):
        lib_id = self.setup_library(client)
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        r = client.patch(f"/v1/libraries/{lib_id}/documents/{doc['id']}")
        assert r.status_code == 422

    def test_delete_document_idempotent(self, client):
        lib_id = self.setup_library(client)
        doc_id = uuid4()
        # deleting non-existent should 404 per router? Router maps NotFoundError to 404
        r = client.delete(f"/v1/libraries/{lib_id}/documents/{doc_id}")
        assert r.status_code in (204, 404)


class TestChunks:
    def setup_library_and_doc(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        return lib_id, doc["id"]

    def test_create_chunk_without_document_id_creates_doc(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        r = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "hello", "metadata": {"m": 1}},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["library_id"] == lib_id
        assert body["text"] == "hello"

    def test_create_chunk_with_document_id(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        r = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "world", "metadata": {}, "document_id": doc_id},
        )
        assert r.status_code == 201
        assert r.json()["document_id"] == doc_id

    def test_create_chunk_missing_body(self, client):
        lib_id, _ = self.setup_library_and_doc(client)
        r = client.post(f"/v1/libraries/{lib_id}/chunks/")
        assert r.status_code == 422

    def test_get_chunk_without_document_id_optional(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "x", "metadata": {}, "document_id": doc_id},
        ).json()
        r = client.get(f"/v1/libraries/{lib_id}/chunks/{created['id']}")
        assert r.status_code == 200
        assert r.json()["id"] == created["id"]

    def test_get_chunk_with_wrong_document_id_404(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "x", "metadata": {}, "document_id": doc_id},
        ).json()
        other_doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()["id"]
        r = client.get(
            f"/v1/libraries/{lib_id}/chunks/{created['id']}",
            params={"document_id": str(other_doc)},
        )
        assert r.status_code == 404

    def test_update_chunk_text_and_metadata(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "before", "metadata": {}, "document_id": doc_id},
        ).json()
        r = client.patch(
            f"/v1/libraries/{lib_id}/chunks/{created['id']}",
            json={"text": "after", "metadata": {"a": 1}},
        )
        assert r.status_code == 200
        out = r.json()
        assert out["text"] == "after"
        assert out["metadata"] == {"a": 1}

    def test_update_chunk_requires_some_field(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "x", "metadata": {}, "document_id": doc_id},
        ).json()
        r = client.patch(f"/v1/libraries/{lib_id}/chunks/{created['id']}", json={})
        assert r.status_code == 422

    def test_delete_chunk_idempotent(self, client):
        lib_id, doc_id = self.setup_library_and_doc(client)
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "x", "metadata": {}, "document_id": doc_id},
        ).json()
        r1 = client.delete(f"/v1/libraries/{lib_id}/chunks/{created['id']}")
        assert r1.status_code == 204
        r2 = client.delete(f"/v1/libraries/{lib_id}/chunks/{created['id']}")
        # Router returns 404 for missing chunk on delete
        assert r2.status_code in (204, 404)


class TestIndex:
    def test_build_index_success(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        r = client.post(f"/v1/libraries/{lib_id}/index")
        # If no chunks added, build should still succeed
        assert r.status_code == 200

    def test_build_index_no_index_400(self, client):
        # Library without index in registry (simulate by new UUID)
        r = client.post(f"/v1/libraries/{uuid4()}/index")
        assert r.status_code == 400


class TestSearch:
    def setup_library_with_chunks(self, client, index_type="linear", index_params=None):
        lib = client.post("/v1/libraries/", json={"name": "lib", "index_type": index_type, "index_params": index_params or {}}).json()
        lib_id = lib["id"]
        created = []
        for text, tag in [("alpha", "x"), ("beta", "y"), ("gamma", "x"), ("delta", "z"), ("epsilon", "y")]:
            resp = client.post(
                f"/v1/libraries/{lib_id}/chunks/",
                json={"text": text, "metadata": {"tag": tag}},
            )
            assert resp.status_code == 201
            created.append(resp.json())
        return lib_id, created

    def test_search_linear_top1_exact_match(self, client):
        lib_id, chunks = self.setup_library_with_chunks(client, index_type="linear")
        # Build index (noop for linear)
        r = client.post(f"/v1/libraries/{lib_id}/index")
        assert r.status_code == 200

        r = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "alpha", "k": 3},
        )
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) >= 1
        assert results[0]["chunk_id"] == chunks[0]["id"]

    def test_search_linear_with_filters(self, client):
        lib_id, chunks = self.setup_library_with_chunks(client, index_type="linear")
        r = client.post(f"/v1/libraries/{lib_id}/index")
        assert r.status_code == 200

        # Query doesn't matter for filter membership; ensure only 'tag' == 'x' returned
        r = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "random-query", "k": 5, "filters": {"tag": "x"}},
        )
        assert r.status_code == 200
        ids_with_tag_x = {c["id"] for c in chunks if c["metadata"].get("tag") == "x"}
        returned_ids = {item["chunk_id"] for item in r.json()["results"]}
        assert returned_ids.issubset(ids_with_tag_x)
        assert len(returned_ids) == len(ids_with_tag_x)

    def test_search_no_index_in_registry_returns_500(self, client):
        from uuid import uuid4
        bogus_lib_id = uuid4()
        r = client.post(
            f"/v1/libraries/{bogus_lib_id}/search",
            json={"query": "q", "k": 2},
        )
        assert r.status_code == 400  # IndexError returns 400, not 500

    def test_search_linear_invalid_k_zero_and_negative(self, client):
        lib_id, _ = self.setup_library_with_chunks(client, index_type="linear")
        r = client.post(f"/v1/libraries/{lib_id}/index")
        assert r.status_code == 200
        # k == 0
        r0 = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "q", "k": 0},
        )
        assert r0.status_code == 422
        # k < 0
        rneg = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "q", "k": -1},
        )
        assert rneg.status_code == 422

    def test_create_linear_with_unused_index_params_and_search(self, client):
        lib = client.post(
            "/v1/libraries/",
            json={"name": "lin-extra", "index_type": "linear", "index_params": {"n_clusters": 10, "foo": "bar"}},
        ).json()
        lib_id = lib["id"]
        # Works end-to-end even if params are unused by LinearIndex
        client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "alpha", "metadata": {}})
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 1})
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

    def test_search_nsw_basic_flow(self, client):
        lib = client.post(
            "/v1/libraries/",
            json={"name": "nsw-lib", "index_type": "nsw", "index_params": {"m": 6, "efConstruction": 16, "efSearch": 32}},
        ).json()
        lib_id = lib["id"]
        created = []
        for text, tag in [("alpha", "x"), ("beta", "y"), ("gamma", "x"), ("delta", "z"), ("epsilon", "y")]:
            resp = client.post(
                f"/v1/libraries/{lib_id}/chunks/",
                json={"text": text, "metadata": {"tag": tag}},
            )
            assert resp.status_code == 201
            created.append(resp.json())

        # NSW index() is a no-op, but call to ensure endpoint works
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200

        # Query for exact 'gamma' match
        r = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "gamma", "k": 3},
        )
        assert r.status_code == 200
        results = r.json()["results"]
        assert 1 <= len(results) <= 3
        gamma_id = next(c["id"] for c in created if c["text"] == "gamma")
        assert results[0]["chunk_id"] == gamma_id

    def test_search_nsw_with_filters(self, client):
        lib = client.post(
            "/v1/libraries/",
            json={"name": "nsw-lib2", "index_type": "nsw"},
        ).json()
        lib_id = lib["id"]
        created = []
        for text, tag in [("alpha", "x"), ("beta", "y"), ("gamma", "x"), ("delta", "z")]:
            created.append(
                client.post(
                    f"/v1/libraries/{lib_id}/chunks/",
                    json={"text": text, "metadata": {"tag": tag}},
                ).json()
            )

        r = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "random", "k": 5, "filters": {"tag": "x"}},
        )
        assert r.status_code == 200
        ids_with_tag_x = {c["id"] for c in created if c["metadata"].get("tag") == "x"}
        returned = {item["chunk_id"] for item in r.json()["results"]}
        assert returned.issubset(ids_with_tag_x)
        assert len(returned) == len(ids_with_tag_x)

    def test_nsw_update_and_search(self, client):
        lib = client.post(
            "/v1/libraries/",
            json={"name": "nsw-lib3", "index_type": "nsw"},
        ).json()
        lib_id = lib["id"]
        c = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "old", "metadata": {}},
        ).json()
        # index is no-op
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        # update chunk text
        assert client.patch(f"/v1/libraries/{lib_id}/chunks/{c['id']}", json={"text": "new"}).status_code == 200
        r = client.post(
            f"/v1/libraries/{lib_id}/search",
            json={"query": "new", "k": 1},
        )
        assert r.status_code == 200
        assert r.json()["results"][0]["chunk_id"] == c["id"]

class TestIVF:
    def test_create_library_ivf_and_index_params_echoed(self, client):
        params = {"n_clusters": 2, "n_probes": 1, "cluster_ratio": 0.5, "probe_ratio": 0.4, "multiplier": 4}
        r = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf", "index_params": params})
        assert r.status_code == 201
        body = r.json()
        assert body["index_type"] == "ivf"
        # index_params stored on library
        assert body.get("index_params") == params

    def test_ivf_search_without_build_uses_unprocessed(self, client):
        lib = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf"}).json()
        lib_id = lib["id"]
        # Add chunks but DO NOT build index
        a = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "alpha", "metadata": {}}).json()
        b = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "beta", "metadata": {}}).json()
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 2})
        assert r.status_code == 200
        top = r.json()["results"][0]["chunk_id"]
        assert top == a["id"]

    def test_ivf_build_and_search_after_ratio(self, client):
        # Create IVF with ratio to determine cluster count (black-box behavior)
        params = {"cluster_ratio": 0.5}
        lib = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf", "index_params": params}).json()
        lib_id = lib["id"]
        # Add 10 chunks
        for i in range(10):
            r = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": f"t{i}", "metadata": {}})
            assert r.status_code == 201
        # Build index
        r = client.post(f"/v1/libraries/{lib_id}/index")
        assert r.status_code == 200
        # Perform a search and ensure sensible results length and validity
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "t5", "k": 3})
        assert r.status_code == 200
        results = r.json()["results"]
        assert 1 <= len(results) <= 3
        # Returned chunk_ids should be valid UUID strings
        import uuid
        for item in results:
            uuid.UUID(item["chunk_id"])  # will raise if invalid

    def test_ivf_search_top1_exact_after_build(self, client):
        lib = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf", "index_params": {"n_probes": 2}}).json()
        lib_id = lib["id"]
        created = []
        for text in ["alpha", "beta", "gamma", "delta", "epsilon"]:
            created.append(client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": text, "metadata": {}}).json())
        r = client.post(f"/v1/libraries/{lib_id}/index")
        assert r.status_code == 200

        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "gamma", "k": 3})
        assert r.status_code == 200
        top = r.json()["results"][0]["chunk_id"]
        gamma_id = next(c["id"] for c in created if c["text"] == "gamma")
        assert top == gamma_id

    def test_ivf_update_chunk_and_rebuild_affects_results(self, client):
        lib = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf"}).json()
        lib_id = lib["id"]
        c = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "old", "metadata": {}}).json()
        # Build index initially
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        # Update chunk text (embedding changes)
        r = client.patch(f"/v1/libraries/{lib_id}/chunks/{c['id']}", json={"text": "zzz"})
        assert r.status_code == 200
        # Rebuild IVF to re-cluster
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "zzz", "k": 1})
        assert r.status_code == 200
        assert r.json()["results"][0]["chunk_id"] == c["id"]

    def test_ivf_search_when_k_exceeds_available(self, client):
        lib = client.post("/v1/libraries/", json={"name": "ivf-lib", "index_type": "ivf"}).json()
        lib_id = lib["id"]
        a = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "alpha", "metadata": {}}).json()
        b = client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "beta", "metadata": {}}).json()
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 10})
        assert r.status_code == 200
        results = r.json()["results"]
        assert len(results) == 2

    def test_ivf_invalid_k_zero_and_negative(self, client):
        lib = client.post("/v1/libraries/", json={"name": "ivf-k", "index_type": "ivf"}).json()
        lib_id = lib["id"]
        r0 = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 0})
        assert r0.status_code == 422
        rneg = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": -5})
        assert rneg.status_code == 422

    def test_ivf_negative_params_are_clamped_and_search_works(self, client):
        params = {"n_clusters": -5, "n_probes": -2, "cluster_ratio": -0.5, "probe_ratio": -0.1, "multiplier": -3}
        lib = client.post("/v1/libraries/", json={"name": "ivf-neg", "index_type": "ivf", "index_params": params}).json()
        lib_id = lib["id"]
        client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "alpha", "metadata": {}})
        client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "beta", "metadata": {}})
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200

        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 2})
        assert r.status_code == 200
        assert len(r.json()["results"]) >= 1

    def test_ivf_unknown_params_ignored_and_search_works(self, client):
        params = {"unknown": "x", "also_bad": 123}
        lib = client.post("/v1/libraries/", json={"name": "ivf-unknown", "index_type": "ivf", "index_params": params}).json()
        lib_id = lib["id"]
        client.post(f"/v1/libraries/{lib_id}/chunks/", json={"text": "alpha", "metadata": {}})
        assert client.post(f"/v1/libraries/{lib_id}/index").status_code == 200
        r = client.post(f"/v1/libraries/{lib_id}/search", json={"query": "alpha", "k": 1})
        assert r.status_code == 200
        assert len(r.json()["results"]) == 1

class TestBadInputs:
    def test_create_library_invalid_enum(self, client):
        r = client.post("/v1/libraries/", json={"name": "x", "index_type": "invalid"})
        assert r.status_code == 422

    def test_create_library_malformed_json(self, client):
        r = client.post(
            "/v1/libraries/",
            data="{not-json}",
            headers={"Content-Type": "application/json"},
        )
        assert r.status_code == 422

    def test_get_library_invalid_uuid(self, client):
        r = client.get("/v1/libraries/not-a-uuid")
        assert r.status_code == 422

    def test_create_chunk_missing_text(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        r = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"metadata": {"a": 1}},
        )
        assert r.status_code == 422

    def test_update_chunk_empty_text(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "ok", "metadata": {}, "document_id": doc["id"]},
        ).json()
        r = client.patch(
            f"/v1/libraries/{lib_id}/chunks/{created['id']}",
            json={"text": ""},
        )
        assert r.status_code == 422

    def test_get_chunk_invalid_document_id_query(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        created = client.post(
            f"/v1/libraries/{lib_id}/chunks/",
            json={"text": "ok", "metadata": {}, "document_id": doc["id"]},
        ).json()
        r = client.get(
            f"/v1/libraries/{lib_id}/chunks/{created['id']}", params={"document_id": "not-a-uuid"}
        )
        assert r.status_code == 422

    def test_create_document_wrong_body_type(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        r = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": "not-a-dict"})
        assert r.status_code == 422

    def test_update_document_wrong_body_type(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        r = client.patch(
            f"/v1/libraries/{lib_id}/documents/{doc['id']}", json={"metadata": "not-a-dict"}
        )
        assert r.status_code == 422

    def test_delete_document_not_found_returns_204(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        r = client.delete(f"/v1/libraries/{lib_id}/documents/{uuid4()}" )
        assert r.status_code == 204

    def test_delete_chunk_not_found_returns_204(self, client):
        lib_id = client.post("/v1/libraries/", json={"name": "lib", "index_type": "linear"}).json()["id"]
        doc = client.post(f"/v1/libraries/{lib_id}/documents/", json={"metadata": {}}).json()
        r = client.delete(f"/v1/libraries/{lib_id}/chunks/{uuid4()}" )
        assert r.status_code == 204


