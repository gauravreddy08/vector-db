from typing import List, Tuple


class KMeans:
    """
    Simple K-Means implementation without external dependencies.

    - Uses cosine distance (1 - cosine_similarity) for assignment
    - Recomputes centroids as arithmetic mean of assigned points
    - Deterministic initialization by picking evenly spaced points
    """

    def __init__(self, n_clusters: int, max_iters: int = 50, tol: float = 1e-4):
        if n_clusters <= 0:
            raise ValueError("n_clusters must be positive")
        self.n_clusters = n_clusters
        self.max_iters = max_iters
        self.tol = tol

        self.centroids: List[List[float]] = []

    def _dot(self, a: List[float], b: List[float]) -> float:
        return sum(x * y for x, y in zip(a, b))

    def _norm(self, a: List[float]) -> float:
        return sum(x * x for x in a) ** 0.5

    def _cosine_distance(self, a: List[float], b: List[float]) -> float:
        denom = self._norm(a) * self._norm(b)
        if denom == 0.0:
            return 1.0
        return 1.0 - (self._dot(a, b) / denom)

    def _mean(self, vectors: List[List[float]]) -> List[float]:
        if not vectors:
            return []
        dim = len(vectors[0])
        sums = [0.0] * dim
        for v in vectors:
            for i in range(dim):
                sums[i] += v[i]
        count = float(len(vectors))
        return [s / count for s in sums]

    def _initialize_centroids(self, X: List[List[float]]) -> List[List[float]]:
        n_samples = len(X)
        k = min(self.n_clusters, n_samples)
        if k == 0:
            return []
        # Deterministic selection: evenly spaced picks in the dataset order
        indices = []
        step = max(1, n_samples // k)
        idx = 0
        seen = set()
        while len(indices) < k:
            if idx >= n_samples:
                idx = (idx % n_samples) + 1
            if idx not in seen:
                indices.append(idx)
                seen.add(idx)
            idx += step
        return [X[i % n_samples][:] for i in indices]

    def fit(self, X: List[List[float]]) -> Tuple[List[List[float]], List[int]]:
        """
        Fit K-Means on the dataset.

        Returns (centroids, labels) where labels are indices in [0, k-1].
        """
        if not X:
            self.centroids = []
            return [], []

        self.centroids = self._initialize_centroids(X)
        k = len(self.centroids)

        labels: List[int] = [0] * len(X)

        for _ in range(self.max_iters):
            # Assignment step
            for i, x in enumerate(X):
                best_c = 0
                best_d = float("inf")
                for c_idx, c in enumerate(self.centroids):
                    d = self._cosine_distance(x, c)
                    if d < best_d:
                        best_d = d
                        best_c = c_idx
                labels[i] = best_c

            # Update step
            clusters: List[List[List[float]]] = [[] for _ in range(k)]
            for lbl, x in zip(labels, X):
                clusters[lbl].append(x)

            new_centroids: List[List[float]] = []
            for c_idx in range(k):
                if clusters[c_idx]:
                    new_centroids.append(self._mean(clusters[c_idx]))
                else:
                    # Keep previous centroid if cluster is empty
                    new_centroids.append(self.centroids[c_idx])

            # Check for convergence (max centroid shift < tol)
            max_shift = 0.0
            for old_c, new_c in zip(self.centroids, new_centroids):
                # pad in case of empty vectors (shouldn't happen with valid data)
                if not old_c or not new_c:
                    continue
                diff = [a - b for a, b in zip(old_c, new_c)]
                shift = self._norm(diff)
                if shift > max_shift:
                    max_shift = shift

            self.centroids = new_centroids
            if max_shift <= self.tol:
                break

        return self.centroids, labels

    def predict(self, X: List[List[float]]) -> List[int]:
        if not self.centroids:
            return [0 for _ in X]
        labels: List[int] = []
        for x in X:
            best_c = 0
            best_d = float("inf")
            for c_idx, c in enumerate(self.centroids):
                d = self._cosine_distance(x, c)
                if d < best_d:
                    best_d = d
                    best_c = c_idx
            labels.append(best_c)
        return labels