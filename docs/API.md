## Overview
Versioned REST API for creating libraries, adding documents/chunks, building custom indexes, and running kNN search with metadata filters.

- Base URL: `/v1`
- Swagger: `/docs`
- Health: `GET /health` → 200

### Quickstart (typical flow)
1) Create a library (choose `linear|ivf|nsw`):
```bash
curl -sX POST http://localhost:8000/v1/libraries/ \
  -H 'Content-Type: application/json' \
  -d '{"name":"demo","index_type":"ivf","index_params": {"n_clusters": 6, "n_probes": 3}}'
```
2) Add chunks (omit `document_id` to auto-create a Document):
```bash
curl -sX POST http://localhost:8000/v1/libraries/<LIB_ID>/chunks/ \
  -H 'Content-Type: application/json' \
  -d '{"text":"alpha","metadata": {"tag":"x"}}'
```
3) Build index (noop for Linear/NSW, required to cluster in IVF):
```bash
curl -sX POST http://localhost:8000/v1/libraries/<LIB_ID>/index
```
4) Search (with optional filters):
```bash
curl -sX POST http://localhost:8000/v1/libraries/<LIB_ID>/search \
  -H 'Content-Type: application/json' \
  -d '{"query":"alpha","k":3,"filters":{"tag":"x"}}'
```

### Indexes at a glance
- Linear: brute-force cosine search. Build step is a noop. Simple and exact; O(n) query.
- IVF: clusters vectors with k-means; probes top clusters at query time. Requires build to cluster; searches unprocessed + processed if not built yet.
- NSW: incremental graph (HNSW-like) with beam search. Build step is a noop; updates maintain graph.

### Filters syntax (exact and operators)
Provide `filters` in `SearchRequest` as either simple equality or operator form:
```json
{"tag":"x"}
```
or
```json
{"rating":{"gte":8.5}, "studio":{"contains":"house"}, "topic":{"in":["anime","ai"]}}
```
Supported operators: `eq` (default), `ne`, `gt`, `gte`, `lt`, `lte`, `contains`, `in`, `nin`.

### Behavior notes
- Creating a chunk without `document_id` auto-creates a `Document` and links it.
- Search requires `k >= 1`. When filters are present, indexes fetch more internally (`multiplier`) then post-filter.
- IVF build step merges buffered chunks, computes centroids, and cluster members. Without a prior build, search still considers unprocessed and current chunks.
- Deleting non-existent resources is safe (idempotent) and may return 204/404 depending on route.

---

## API Reference

Base URL: `/v1`

### Health
- GET `/health` → 200

### Libraries
- GET `/libraries/` → 200
  - Response: `List[UUID]`

- GET `/libraries/{library_id}` → 200
  - Response: `LibraryResponse`
    - `id: UUID`, `name: str`, `created_at: datetime`, `metadata: Dict[str, Any]`
    - `index_type: str` (one of `linear|ivf|nsw`), `index_params: Dict[str, Any] | null`
    - `documents: List[UUID]`

- POST `/libraries/` → 201
  - Body `LibraryCreateRequest`
    - `name: str`
    - `index_type: linear|ivf|nsw` (default `linear`)
    - `index_params?: Dict[str, Any]` (IVF/NSW knobs)
    - `metadata?: Dict[str, Any]`
  - Response: `LibraryResponse`

- PATCH `/libraries/{library_id}` → 200
  - Body `LibraryUpdateRequest` (at least one field required)
    - `name?: str`
    - `metadata?: Dict[str, Any]`
  - Response: `LibraryResponse`

- DELETE `/libraries/{library_id}` → 200

### Documents
- POST `/libraries/{library_id}/documents/` → 201
  - Body `DocumentCreateRequest`
    - `metadata?: Dict[str, Any]`
  - Response: `DocumentResponse`
    - `id: UUID`, `library_id: UUID`, `chunks: List[UUID]`, `metadata: Dict[str, Any]`, `created_at: datetime`

- GET `/libraries/{library_id}/documents/{document_id}` → 200
  - Response: `DocumentResponse`

- PATCH `/libraries/{library_id}/documents/{document_id}` → 200
  - Body `DocumentUpdateRequest`
    - `metadata: Dict[str, Any]`
  - Response: `DocumentResponse`

- DELETE `/libraries/{library_id}/documents/{document_id}` → 204

### Chunks
- POST `/libraries/{library_id}/chunks/` → 201
  - Body `ChunkCreateRequest`
    - `text: str`
    - `metadata?: Dict[str, Any]`
    - `document_id?: UUID` (if omitted, a new Document is created automatically)
    - `document_metadata?: Dict[str, Any]` (used when auto-creating a Document)
  - Response: `ChunkResponse`
    - `id: UUID`, `document_id: UUID`, `library_id: UUID`, `text: str`, `metadata: Dict[str, Any]`, `created_at: datetime`

- GET `/libraries/{library_id}/chunks/{chunk_id}` → 200
  - Query: `document_id?: UUID` (optional scope validation)
  - Response: `ChunkResponse`

- PATCH `/libraries/{library_id}/chunks/{chunk_id}` → 200
  - Query: `document_id?: UUID`
  - Body `ChunkUpdateRequest` (at least one field required)
    - `text?: str`
    - `metadata?: Dict[str, Any]`
  - Response: `ChunkResponse`

- DELETE `/libraries/{library_id}/chunks/{chunk_id}` → 204
  - Query: `document_id?: UUID`

### Indexing & Search
- POST `/libraries/{library_id}/index` → 200
  - Response: `IndexResponse` `{ library_id: UUID, message: str, last_indexed_at: datetime }`

- POST `/libraries/{library_id}/search` → 200
  - Body `SearchRequest`
    - `query: str`
    - `k: int (>=1)`
    - `filters?: Dict[str, Any]` (exact-match metadata filters)
  - Response `SearchResponse`
    - `library_id: UUID, query: str, k: int, filters?: Dict[str, Any]`
    - `results: List[SearchResult]`
      - `chunk_id: UUID, score: float, chunk: ChunkResponse`

Notes
- Content type: `application/json`
- Errors follow standard HTTP codes with `detail` messages.

### Minimal end-to-end example
```bash
# 1) Create IVF library
LIB=$(curl -sX POST http://localhost:8000/v1/libraries/ -H 'Content-Type: application/json' \
  -d '{"name":"mix","index_type":"ivf","index_params":{"cluster_ratio":0.5,"n_probes":2}}' | jq -r .id)

# 2) Add chunks (auto-doc)
curl -sX POST http://localhost:8000/v1/libraries/$LIB/chunks/ -H 'Content-Type: application/json' \
  -d '{"text":"alpha","metadata":{"tag":"x"}}' >/dev/null
curl -sX POST http://localhost:8000/v1/libraries/$LIB/chunks/ -H 'Content-Type: application/json' \
  -d '{"text":"beta","metadata":{"tag":"y"}}' >/dev/null

# 3) Build index (clusters)
curl -sX POST http://localhost:8000/v1/libraries/$LIB/index >/dev/null

# 4) Search with filter
curl -sX POST http://localhost:8000/v1/libraries/$LIB/search -H 'Content-Type: application/json' \
  -d '{"query":"alpha","k":3,"filters":{"tag":"x"}}'
```

