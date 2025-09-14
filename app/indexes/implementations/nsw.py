from typing import Callable, List, Tuple, Dict, Any, Optional, Set
from uuid import UUID
import heapq

from app.indexes.base import BaseIndex
from app.indexes.filters.engine import Filters
from app.utils.similarity import cosine_similarity
from app.config import get_nsw_config

from readerwriterlock import rwlock


class NSWIndex(BaseIndex, Filters):
    def __init__(self,
                 m: Optional[int] = None,
                 efConstruction: Optional[int] = None,
                 efSearch: Optional[int] = None,
                 similarity_function: Callable[[List[float], List[float]], float] = cosine_similarity,
                 multiplier: Optional[int] = None):
        super().__init__()

        # Load configuration
        config = get_nsw_config()

        self._chunks: Dict[UUID, List[float]] = {}
        self._metadata: Dict[UUID, Dict[str, Any]] = {}
        self._graph: Dict[UUID, Set[UUID]] = {}
        self._entry_point: Optional[UUID] = None

        self._lock = rwlock.RWLockFair()
        self._similarity_function = similarity_function

        # Hyperparameters
        self.M: int = max(1, int(m if m is not None else config.get("M", 8)))
        self.efConstruction: int = max(1, int(efConstruction if efConstruction is not None else config.get("efConstruction", 32)))
        self.efSearch: int = max(1, int(efSearch if efSearch is not None else config.get("efSearch", 64)))
        self.multiplier: int = int(multiplier if multiplier is not None else config.get("multiplier", 3))

    def index(self) -> bool:
        # NSW is incremental; nothing to build
        return True

    def _beam_search(self, query_embedding: List[float], ef: int, start_ids: List[UUID]) -> List[Tuple[UUID, float]]:
        if not start_ids:
            return []

        visited = set()
        candidates = []  # max-heap via negative sim
        results = []     # min-heap by sim

        # Seed with provided starts
        for sid in start_ids:
            if sid not in self._chunks:
                continue
            sim = self._similarity_function(self._chunks[sid], query_embedding)
            heapq.heappush(candidates, (-sim, sid))
            heapq.heappush(results, (sim, sid))
            if len(results) > ef:
                heapq.heappop(results)

        while candidates:
            neg_sim, node_id = heapq.heappop(candidates)
            current_sim = -neg_sim

            if node_id in visited:
                continue
            visited.add(node_id)

            if len(results) >= ef and current_sim < results[0][0]:
                break

            for neighbor in self._graph.get(node_id, set()):
                if neighbor in visited:
                    continue
                sim = self._similarity_function(self._chunks[neighbor], query_embedding)
                if len(results) < ef or sim > results[0][0]:
                    heapq.heappush(candidates, (-sim, neighbor))
                    heapq.heappush(results, (sim, neighbor))
                    if len(results) > ef:
                        heapq.heappop(results)

        out = []
        while results:
            sim, nid = heapq.heappop(results)
            out.append((nid, sim))
        out.sort(key=lambda x: x[1], reverse=True)
        return out

    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        with self._lock.gen_wlock():
            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata

            if self._entry_point is None:
                self._graph[chunk_id] = set()
                self._entry_point = chunk_id
                return

            # Find construction neighbors
            neighbors_ranked = self._beam_search(embedding, self.efConstruction, [self._entry_point])
            selected = []
            for nid, _ in neighbors_ranked:
                if nid == chunk_id:
                    continue
                selected.append(nid)
                if len(selected) >= self.M:
                    break

            # Connect bidirectionally
            if chunk_id not in self._graph:
                self._graph[chunk_id] = set()
            for nid in selected:
                if nid not in self._graph:
                    self._graph[nid] = set()
                self._graph[chunk_id].add(nid)
                self._graph[nid].add(chunk_id)

    def search(self, query_embedding: List[float], k: int, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        with self._lock.gen_rlock():
            if self._entry_point is None:
                return []

            fetch_count = k * self.multiplier if filters else k
            ef = max(self.efSearch, fetch_count)
            ranked = self._beam_search(query_embedding, ef, [self._entry_point])

            results = []
            for nid, sim in ranked:
                if self._matches_filters(nid, filters or {}):
                    results.append((nid, sim))
                if len(results) >= k:
                    break
            return results

    def delete(self, chunk_id: UUID) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks:
                return False

            # Step 1-3: remove connections and node
            neighbors = set(self._graph.get(chunk_id, set()))
            for nbr in neighbors:
                if nbr in self._graph:
                    self._graph[nbr].discard(chunk_id)

            if chunk_id in self._graph:
                del self._graph[chunk_id]
            if chunk_id in self._metadata:
                del self._metadata[chunk_id]
            del self._chunks[chunk_id]

            # Adjust entry point if needed
            if self._entry_point == chunk_id:
                self._entry_point = next(iter(self._chunks.keys()), None)

            # Step 4: repair each affected neighbor
            if not self._chunks or self._entry_point is None:
                return True

            for u in neighbors:
                if u not in self._chunks:
                    continue
                # Remove all current edges for u (already removed edge to chunk_id)
                for v in list(self._graph.get(u, set())):
                    self._graph[v].discard(u)
                self._graph[u] = set()

                # Reconnect u
                ranked = self._beam_search(self._chunks[u], self.efConstruction, [self._entry_point])
                selected = []
                for nid, _ in ranked:
                    if nid == u:
                        continue
                    selected.append(nid)
                    if len(selected) >= self.M:
                        break
                for nid in selected:
                    if nid not in self._graph:
                        self._graph[nid] = set()
                    self._graph[u].add(nid)
                    self._graph[nid].add(u)

            return True

    def update(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks:
                return False

            # Update vector and metadata
            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata

            # Recompute neighbors for this node
            # Detach current connections
            for v in list(self._graph.get(chunk_id, set())):
                self._graph[v].discard(chunk_id)
            self._graph[chunk_id] = set()

            if self._entry_point is None:
                self._entry_point = chunk_id
                return True

            ranked = self._beam_search(embedding, self.efConstruction, [self._entry_point])
            selected = []
            for nid, _ in ranked:
                if nid == chunk_id:
                    continue
                selected.append(nid)
                if len(selected) >= self.M:
                    break
            for nid in selected:
                if nid not in self._graph:
                    self._graph[nid] = set()
                self._graph[chunk_id].add(nid)
                self._graph[nid].add(chunk_id)
            return True