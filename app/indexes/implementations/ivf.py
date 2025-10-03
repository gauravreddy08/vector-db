from typing import Callable, List, Tuple, Dict, Any, Optional, Set
from uuid import UUID
import heapq

from app.indexes.base import BaseIndex
from app.indexes.filters.engine import Filters
from app.utils.similarity import cosine_similarity
from app.utils.helper_functions.kmeans import KMeans
from app.config import get_ivf_config

from readerwriterlock import rwlock


class IVFIndex(BaseIndex, Filters):
    def __init__(self,
                 n_clusters: Optional[int] = None,
                 similarity_function: Callable[[List[float], List[float]], float] = cosine_similarity,
                 n_probes: Optional[int] = None,
                 cluster_ratio: Optional[float] = None,
                 probe_ratio: Optional[float] = None,
                 multiplier: Optional[int] = None):
        super().__init__()

        config = get_ivf_config()
        
        self._chunks: Dict[UUID, List[float]] = {}
        self._unprocessed_chunks: Dict[UUID, List[float]] = {}
        self._metadata: Dict[UUID, Dict[str, Any]] = {}

        self._centroids: List[List[float]] = []
        self._cluster_members: List[Set[UUID]] = []

        self._lock = rwlock.RWLockFair()
        self._similarity_function = similarity_function

        self._kmeans: Optional[KMeans] = None

        # Params for IVF Configuration
        # For Post filtering (get more (k*multiplier) results and then apply filters)
        self.multiplier = multiplier if multiplier is not None else config["multiplier"] 

        # Number of clusters to cluster the chunks into 
        self._explicit_n_clusters = n_clusters 

        # used when no explicit number of clusters is provided. takes a ratio of the total number of chunks to cluster the chunks into 
        self._cluster_ratio = max(0.0, cluster_ratio if cluster_ratio is not None else config["cluster_ratio"]) 

        # Number of probes to probe during search
        self._explicit_n_probes = n_probes

        # used when no explicit number of probes is provided. takes a ratio of the total number of clusters to probe during search
        self._probe_ratio = max(0.0, probe_ratio if probe_ratio is not None else config["probe_ratio"]) 
        
        # Number of probes to probe during search
        self._computed_n_probes: Optional[int] = None

    def add(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> None:
        with self._lock.gen_wlock():
            self._unprocessed_chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
    
    def index(self) -> bool:
        with self._lock.gen_wlock():
            if self._unprocessed_chunks:
                self._chunks.update(self._unprocessed_chunks)
                self._unprocessed_chunks = {}

            if not self._chunks:
                self._centroids = []
                self._cluster_members = []
                return True

            chunk_ids = list(self._chunks.keys())
            embeddings = [self._chunks[cid] for cid in chunk_ids]

            n_points = len(embeddings)
            effective_k = self._explicit_n_clusters
            if effective_k is None:
                effective_k = max(1, int(round(n_points * self._cluster_ratio)))
            effective_k = max(1, min(effective_k, n_points))

            self._kmeans = KMeans(effective_k)

            centroids, labels = self._kmeans.fit(embeddings)
            if not centroids:
                self._centroids = []
                self._cluster_members = []
                return True

            k = len(centroids)
            cluster_members = [set() for _ in range(k)]
            for cid, lbl in zip(chunk_ids, labels):
                if 0 <= lbl < k:
                    cluster_members[lbl].add(cid)

            self._centroids = centroids
            self._cluster_members = cluster_members

            if self._explicit_n_probes is not None:
                probes = int(self._explicit_n_probes)
            else:
                probes = int(max(1, round(len(self._centroids) * self._probe_ratio)))
            self._computed_n_probes = max(1, min(probes, len(self._centroids)))
            return True
    
    def search(self, query_embedding: List[float], k: int, filters: Optional[Dict[str, Any]] = None) -> List[Tuple[UUID, float]]:
        with self._lock.gen_rlock():
            fetch_count = k * self.multiplier if filters else k

            if not self._centroids:
                search_space = {**self._chunks, **self._unprocessed_chunks}
                results = self._brute_force_search(search_space, query_embedding, fetch_count, filters)
                return results[:k]

            total_clusters = len(self._centroids)

            if self._computed_n_probes is not None and self._computed_n_probes > 0:
                probes = min(max(1, self._computed_n_probes), total_clusters)
            else:
                probes = max(1, int(round(total_clusters * self._probe_ratio)))
                probes = min(probes, total_clusters)

            ranked = []
            for idx, centroid in enumerate(self._centroids):
                sim = self._similarity_function(centroid, query_embedding)
                ranked.append((sim, idx))
            
            ranked.sort(key=lambda x: x[0], reverse=True)
            ranked_indices = [idx for _, idx in ranked]

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
                
                for members in self._cluster_members:
                    members.discard(chunk_id)
            if chunk_id in self._metadata:
                del self._metadata[chunk_id]
            return existed
        
    def update(self, chunk_id: UUID, embedding: List[float], metadata: Dict[str, Any]) -> bool:
        with self._lock.gen_wlock():
            if chunk_id not in self._chunks and chunk_id not in self._unprocessed_chunks:
                return False

            if chunk_id in self._chunks:
                del self._chunks[chunk_id]
                for members in self._cluster_members:
                    members.discard(chunk_id)
            self._unprocessed_chunks[chunk_id] = embedding
            self._metadata[chunk_id] = metadata
            return True