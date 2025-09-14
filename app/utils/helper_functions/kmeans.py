from typing import List, Tuple, Optional

import numpy as np

from app.config import get_kmeans_config


class KMeans:
    """
    Minimal cosine K-Means.

    - Uses cosine distance (1 - cosine similarity) for assignment
    - Recomputes centroids as arithmetic mean of assigned points
    - Random initialization by sampling k unique points
    """

    def __init__(self, n_clusters: int, max_iters: Optional[int] = None, tol: Optional[float] = None):
        if n_clusters <= 0:
            raise ValueError("n_clusters must be positive")

        # Load configuration
        config = get_kmeans_config()

        self.n_clusters = n_clusters
        self.max_iters = max_iters if max_iters is not None else config["max_iters"]
        self.tol = tol if tol is not None else config["tolerance"]

        self.centroids: List[List[float]] = []

    def _normalize(self, X: np.ndarray) -> np.ndarray:
        if X.size == 0:
            return X
        norms = np.linalg.norm(X, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        return X / norms

    def fit(self, X: List[List[float]]) -> Tuple[List[List[float]], List[int]]:
        """
        Fit K-Means on the dataset.

        Returns (centroids, labels) where labels are indices in [0, k-1].
        """
        if not X:
            self.centroids = []
            return [], []

        data = np.asarray(X, dtype=float)
        n_samples = data.shape[0]
        k = max(1, min(self.n_clusters, n_samples))

        # Random initialization: sample k unique points (no replacement)
        indices = np.random.choice(n_samples, size=k, replace=False)
        centroids = data[indices].copy()

        labels = np.zeros(n_samples, dtype=int)

        for _ in range(self.max_iters):
            # Assignment step via cosine similarity (argmax similarity == argmin distance)
            data_n = self._normalize(data)
            centroids_n = self._normalize(centroids)
            sims = data_n @ centroids_n.T
            labels = np.argmax(sims, axis=1)

            # Update step
            new_centroids = centroids.copy()
            max_shift = 0.0
            for ci in range(k):
                members = data[labels == ci]
                if members.size > 0:
                    candidate = members.mean(axis=0)
                    shift = float(np.linalg.norm(candidate - centroids[ci]))
                    if shift > max_shift:
                        max_shift = shift
                    new_centroids[ci] = candidate

            centroids = new_centroids
            if max_shift <= self.tol:
                break

        self.centroids = centroids.tolist()
        return self.centroids, labels.tolist()

    def predict(self, X: List[List[float]]) -> List[int]:
        if not self.centroids:
            return [0 for _ in X]
        if not X:
            return []
        data = np.asarray(X, dtype=float)
        centroids = np.asarray(self.centroids, dtype=float)
        data_n = self._normalize(data)
        centroids_n = self._normalize(centroids)
        sims = data_n @ centroids_n.T
        labels = np.argmax(sims, axis=1)
        return labels.tolist()