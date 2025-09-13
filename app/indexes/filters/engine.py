from typing import Dict, Any
from uuid import UUID

class Filters:
    def __init__(self):
        if not hasattr(self, '_metadata'):
            self._metadata: Dict[UUID, Dict[str, Any]] = {}
    
    def _matches_filters(self, chunk_id: UUID, filters: Dict[str, Any]) -> bool:
        """Check if chunk matches all filter criteria."""
        if not filters:
            return True
            
        chunk_metadata = self._metadata.get(chunk_id, {})
        normalized_filters = self._normalize_filters(filters)
        
        for field_name, filter_spec in normalized_filters.items():
            if not self._matches_field_filter(chunk_metadata, field_name, filter_spec):
                return False
        
        return True
    
    def _normalize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Convert simple filters to operator format."""
        normalized = {}
        for field_name, filter_value in filters.items():
            if isinstance(filter_value, dict):
                normalized[field_name] = filter_value
            else:
                normalized[field_name] = {"eq": filter_value}
        return normalized
    
    def _matches_field_filter(self, metadata: Dict[str, Any], field_name: str, filter_spec: Dict[str, Any]) -> bool:
        """Check if a single field matches the filter specification."""
        field_value = metadata.get(field_name)
        if field_value is None:
            return False
        
        for operator, expected_value in filter_spec.items():
            if not self._apply_operator(field_value, operator, expected_value):
                return False
        return True
    
    def _apply_operator(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Apply a single operator comparison."""
        try:
            if operator == "eq":
                return field_value == expected_value
            elif operator == "ne":
                return field_value != expected_value
            elif operator == "gt":
                return field_value > expected_value
            elif operator == "gte":
                return field_value >= expected_value
            elif operator == "lt":
                return field_value < expected_value
            elif operator == "lte":
                return field_value <= expected_value
            elif operator == "contains":
                return str(expected_value).lower() in str(field_value).lower()
            elif operator == "in":
                return isinstance(expected_value, list) and field_value in expected_value
            elif operator == "nin":
                return isinstance(expected_value, list) and field_value not in expected_value
            else:
                return True
        except (TypeError, ValueError):
            return False