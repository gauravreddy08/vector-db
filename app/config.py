"""
Configuration file for vector database hyperparameters.

This module contains the hardcoded hyperparameters used across different
indexing algorithms, making them easily configurable and maintainable.
"""

from typing import Dict, Any


class IndexConfig:
    """Configuration for indexing algorithms."""
    
    # IVF (Inverted File) Index Configuration
    IVF = {
        "cluster_ratio": 0.05,  # Ratio of total points to use as clusters
        "probe_ratio": 0.2,    # Ratio of clusters to probe during search
        "multiplier": 3,        # Multiplier for results when filters are applied
    }
    
    # Linear Index Configuration
    LINEAR = {
        "multiplier": 3,        # Multiplier for results when filters are applied
    }
    
    # NSW (Navigable Small World) Index Configuration
    NSW = {
        "M": 8,                 # Number of bi-directional connections per insertion
        "efConstruction": 32,   # Beam size during construction
        "efSearch": 64,         # Beam size during query
        "multiplier": 3,        # Multiplier for results when filters are applied
    }
    
    # KMeans Configuration
    KMEANS = {
        "max_iters": 50,        # Maximum number of iterations
        "tolerance": 1e-4,      # Convergence tolerance
    }


# Convenience functions for accessing configurations
def get_ivf_config() -> Dict[str, Any]:
    """Get IVF index configuration."""
    return IndexConfig.IVF.copy()


def get_linear_config() -> Dict[str, Any]:
    """Get Linear index configuration."""
    return IndexConfig.LINEAR.copy()


def get_kmeans_config() -> Dict[str, Any]:
    """Get KMeans configuration."""
    return IndexConfig.KMEANS.copy()


def get_nsw_config() -> Dict[str, Any]:
    """Get NSW index configuration."""
    return IndexConfig.NSW.copy()
