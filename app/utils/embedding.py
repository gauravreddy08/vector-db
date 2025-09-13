import cohere
from typing import List, Literal, Optional
import os
import re

from dotenv import load_dotenv
load_dotenv(override=True)

# Valid dimensions for embed-v4 and newer models
VALID_DIMENSIONS = [256, 512, 1024, 1536]
DEFAULT_DIMENSION = 1536

class CohereEmbedding:
    """
    Cohere embedding utility with dimension control for embed-v4 and newer models.
    
    Supports dimensions: 256, 512, 1024, 1536 (default: 1536)
    Only available for embed-v4 and newer models.
    """
    
    def __init__(self, model: str = "embed-v4.0"):
        self.model = model
        self.co = cohere.ClientV2()
        self.valid_dimensions = [256, 512, 1024, 1536]
    
    def embed(self, text: str, input_type: Literal["search_document", "search_query"] = "search_document", dimension: int = 1024) -> List[float]:
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        if dimension not in self.valid_dimensions:
            raise ValueError(f"Invalid dimension {dimension}. Valid dimensions are: {self.valid_dimensions}")
        
        try:
            response = self.co.embed(
                model=self.model,
                texts=[text],
                input_type=input_type,
                embedding_types=["float"],
                output_dimension=dimension
            )
            return response.embeddings.float_[0]
            
        except Exception as e:
            raise Exception(f"Failed to generate embedding: {str(e)}")