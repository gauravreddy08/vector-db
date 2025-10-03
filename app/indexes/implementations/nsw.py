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

        config = get_nsw_config()

        self._chunks: Dict[UUID, List[float]] = {}
        self._metadata: Dict[UUID, Dict[str, Any]] = {}
        self._graph: Dict[UUID, Set[UUID]] = {}
        self._entry_point: Optional[UUID] = None

        self._lock = rwlock.RWLockFair()
        self._similarity_function = similarity_function

        self.M: int = max(1, int(m if m is not None else config.get("M", 8)))
        self.efConstruction: int = max(1, int(efConstruction if efConstruction is not None else config.get("efConstruction", 32)))
        self.efSearch: int = max(1, int(efSearch if efSearch is not None else config.get("efSearch", 64)))
        self.multiplier: int = int(multiplier if multiplier is not None else config.get("multiplier", 3))

    def index(self) -> bool:
        return True

    def _beam_search(self, query_embedding: List[float], ef: int, start_ids: List[UUID]) -> List[Tuple[UUID, float]]:
        if not start_ids:
            return []

        visited = set()
        candidates = [] # Sources for BFS (Beam Search) [maxheap] [-current_sim, node_id]
        results = [] # Final results, is bounded by ef (minheap) [current_sim, node_id]
        candidates_set = set()  # Track whats already in candidates queue

        # Initialize with start_ids, avoiding duplicates
        for sid in start_ids:
            if sid not in self._chunks:
                continue
            sim = self._similarity_function(self._chunks[sid], query_embedding)
            heapq.heappush(candidates, (-sim, sid))
            candidates_set.add(sid)

        while candidates:
            neg_sim, node_id = heapq.heappop(candidates)
            current_sim = -neg_sim
            candidates_set.discard(node_id)

            if node_id in visited:
                continue
            visited.add(node_id)

            # Add the processed node to results (unique by visited)
            heapq.heappush(results, (current_sim, node_id))
            if len(results) > ef:
                heapq.heappop(results)

            if len(results) >= ef and current_sim < results[0][0]:
                break

            for neighbor in self._graph.get(node_id, set()):
                if neighbor in visited or neighbor in candidates_set:
                    continue
                sim = self._similarity_function(self._chunks[neighbor], query_embedding)
                heapq.heappush(candidates, (-sim, neighbor))
                candidates_set.add(neighbor)

        # Build sorted output from unique processed nodes
        out_pairs = sorted(results, key=lambda x: x[0], reverse=True)
        return [(nid, sim) for (sim, nid) in out_pairs]

    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        with self._lock.gen_wlock():
            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata

            if self._entry_point is None:
                self._graph[chunk_id] = set()
                self._entry_point = chunk_id
                return

            neighbors_ranked = self._beam_search(embedding, self.efConstruction, [self._entry_point])
            selected = []
            for nid, _ in neighbors_ranked:
                if nid == chunk_id:
                    continue
                selected.append(nid)
                if len(selected) >= self.M:
                    break

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

            neighbors = set(self._graph.get(chunk_id, set()))
            for nbr in neighbors:
                if nbr in self._graph:
                    self._graph[nbr].discard(chunk_id)

            if chunk_id in self._graph:
                del self._graph[chunk_id]
            if chunk_id in self._metadata:
                del self._metadata[chunk_id]
            del self._chunks[chunk_id]

            if self._entry_point == chunk_id:
                self._entry_point = next(iter(self._chunks.keys()), None)

            if not self._chunks or self._entry_point is None:
                return True

            for u in neighbors:
                if u not in self._chunks:
                    continue
                for v in list(self._graph.get(u, set())):
                    self._graph[v].discard(u)
                self._graph[u] = set()

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

            self._chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata

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