from typing import Callable, List, Tuple, Dict, Any, Optional, Set
from uuid import UUID
import heapq

from app.indexes.base import BaseIndex
from app.indexes.filters.engine import Filters
from app.utils.similarity import cosine_similarity
from app.utils.helper_functions.kmeans import KMeans

from readerwriterlock import rwlock


class IVFIndex(BaseIndex, Filters):
    def __init__(self,
                 n_clusters: Optional[int] = None,
                 similarity_function: Callable[[List[float], List[float]], float] = cosine_similarity,
                 default_n_probes: Optional[int] = None,
                 n_probes: Optional[int] = None,
                 cluster_ratio: float = 0.05,
                 probe_ratio: float = 0.2,
                 multiplier: int = 3):
        super().__init__()

        self._chunks: Dict[UUID, List[float]] = {}

        self._unprocessed_chunks: Dict[UUID, List[float]] = {}

        self._metadata: Dict[UUID, Dict[str, Any]] = {}

        # IVF structures
        self._centroids: List[List[float]] = []
        self._cluster_members: List[Set[UUID]] = []  

        self._lock = rwlock.RWLockFair()
        self._similarity_function = similarity_function

        # KMeans instance will be (re)initialized at index() once we know effective k
        self._kmeans: Optional[KMeans] = None

        # Configuration
        self.multiplier = multiplier  # Fetch extra when filters are applied
        self._cluster_ratio = max(0.0, cluster_ratio)
        self._probe_ratio = max(0.0, probe_ratio)
        # Explicit overrides (can be None to enable computed defaults)
        self._explicit_n_clusters = n_clusters
        self._explicit_default_n_probes = default_n_probes if default_n_probes is not None else n_probes
        # Computed at last index() run
        self._computed_n_probes: Optional[int] = None

    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        with self._lock.gen_wlock():
            self._unprocessed_chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
    
    def index(self) -> bool:
        with self._lock.gen_wlock():
            # Merge buffered chunks
            if self._unprocessed_chunks:
                self._chunks.update(self._unprocessed_chunks)
                self._unprocessed_chunks = {}

            if not self._chunks:
                # Nothing to index
                self._centroids = []
                self._cluster_members = []
                return True

            # Prepare data for kmeans
            chunk_ids = list(self._chunks.keys())
            embeddings = [self._chunks[cid] for cid in chunk_ids]

            # Determine effective number of clusters
            n_points = len(embeddings)
            effective_k = self._explicit_n_clusters
            if effective_k is None:
                effective_k = max(1, int(round(n_points * self._cluster_ratio)))
            effective_k = max(1, min(effective_k, n_points))

            # Initialize KMeans with effective_k
            self._kmeans = KMeans(effective_k)

            centroids, labels = self._kmeans.fit(embeddings)
            if not centroids:
                self._centroids = []
                self._cluster_members = []
                return True

            k = len(centroids)
            cluster_members = [set() for _ in range(k)]
            for cid, lbl in zip(chunk_ids, labels):
                # Guard for label being out of range due to any bug
                if 0 <= lbl < k:
                    cluster_members[lbl].add(cid)

            self._centroids = centroids
            self._cluster_members = cluster_members

            # Compute default n_probes if not explicitly provided
            if self._explicit_default_n_probes is not None:
                probes = int(self._explicit_default_n_probes)
            else:
                probes = int(max(1, round(len(self._centroids) * self._probe_ratio)))
            self._computed_n_probes = max(1, min(probes, len(self._centroids)))
            return True
    
    def search(self, query_embedding: List[float], k: int, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        with self._lock.gen_rlock():
            fetch_count = k * self.multiplier if filters else k

            # If no clusters, search over all data (processed + unprocessed)
            if not self._centroids:
                search_space = {**self._chunks, **self._unprocessed_chunks}
                results = self._brute_force_search(search_space, query_embedding, fetch_count, filters)
                return results[:k]

            total_clusters = len(self._centroids)

            # Determine initial probes from computed or ratio
            if self._computed_n_probes is not None and self._computed_n_probes > 0:
                probes = min(max(1, self._computed_n_probes), total_clusters)
            else:
                probes = max(1, int(round(total_clusters * self._probe_ratio)))
                probes = min(probes, total_clusters)

            # Rank all clusters by similarity (desc)
            ranked = []
            for idx, centroid in enumerate(self._centroids):
                sim = self._similarity_function(centroid, query_embedding)
                ranked.append((sim, idx))
            
            ranked.sort(key=lambda x: x[0], reverse=True)
            ranked_indices = [idx for _, idx in ranked]

            # Build search space: probe initial n_probes clusters first
            search_space = dict(self._unprocessed_chunks)

            for idx in ranked_indices:
                if 0 <= idx < len(self._cluster_members):
                    for cid in self._cluster_members[idx]:
                        emb = self._chunks.get(cid)
                        if emb is not None:
                            search_space[cid] = emb
                if len(search_space) >= fetch_count and idx + 1 >= probes:
                    break

            results = self._brute_force_search(search_space, query_embedding, fetch_count, filters)
            return results[:k]

    def _brute_force_search(self, 
                            search_space: Dict[UUID, List[float]],
                            query_embedding: List[float], 
                            k: int, 
                            filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        
        # Slightly optimized O(n log k)
        heap = []
        for chunk_id, embedding in search_space.items():
            similarity = self._similarity_function(embedding, query_embedding)
            heapq.heappush(heap, (similarity, chunk_id))
            if len(heap) > k:
                heapq.heappop(heap)

        results = []
        while heap:
            similarity, chunk_id = heapq.heappop(heap)
            if self._matches_filters(chunk_id, filters):
                results.append((chunk_id, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:k]
        
    def delete(self, chunk_id: UUID) -> bool:
        with self._lock.gen_wlock():
            existed = False
            if chunk_id in self._unprocessed_chunks:
                del self._unprocessed_chunks[chunk_id]
                existed = True
            if chunk_id in self._chunks:
                del self._chunks[chunk_id]
                existed = True
                # Remove from cluster membership if present
                for members in self._cluster_members:
                    members.discard(chunk_id)
            if chunk_id in self._metadata:
                del self._metadata[chunk_id]
            return existed
        
    def update(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks and chunk_id not in self._unprocessed_chunks:
                return False

            # Move to unprocessed with new embedding to be re-indexed later
            if chunk_id in self._chunks:
                del self._chunks[chunk_id]
                for members in self._cluster_members:
                    members.discard(chunk_id)
            self._unprocessed_chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
            return True