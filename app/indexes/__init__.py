"""
Vector indexes module.

This module provides a modular architecture for vector indexing algorithms.
"""

from .base import BaseIndex
from .factory import create_index
from .filters.engine import Filters
from .implementations.linear import LinearIndex
from .implementations.ivf import IVFIndex

__all__ = [
    'BaseIndex',
    'Filters', 
    'LinearIndex',
    'IVFIndex',
    'create_index'
]
