
from app.indexes.base import BaseIndex
from app.indexes.implementations.linear import LinearIndex
from app.indexes.implementations.ivf import IVFIndex
from app.domain.models import IndexModel

def create_index(index_type: str, params: dict | None = None) -> BaseIndex:
    """
    Factory function to create vector index instances based on type.
    
    Args:
        index_type: The type of index to create (e.g., "linear")
        
    Returns:
        An instance of the requested index type
        
    Raises:
        ValueError: If the index type is not supported
    """
    if index_type == IndexModel.LINEAR.value:
        return LinearIndex()
    if index_type == IndexModel.IVF.value:
        # Let IVFIndex own its defaults; pass through only supported params
        allowed = {"n_clusters", "n_probes", "cluster_ratio", "probe_ratio", "multiplier"}
        safe_params = {k: v for k, v in (params or {}).items() if k in allowed}
        return IVFIndex(**safe_params)
    else:
        raise ValueError(f"Unsupported index type: {index_type}")
