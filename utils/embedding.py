#!/usr/bin/env python3
"""
Embedding Model Utility - Cache SentenceTransformer model globally
"""

from sentence_transformers import SentenceTransformer
from typing import Optional

# Global cache for embedding model
_embedding_model: Optional[SentenceTransformer] = None
_model_name: Optional[str] = None

def get_embedding_model(model_name: str = 'all-MiniLM-L6-v2') -> SentenceTransformer:
    """
    Get cached SentenceTransformer model.
    Model is loaded once and reused for all subsequent calls.
    
    Args:
        model_name: Name of the SentenceTransformer model
        
    Returns:
        Cached SentenceTransformer model
    """
    global _embedding_model, _model_name
    
    # If model is already loaded and same name, return cached
    if _embedding_model is not None and _model_name == model_name:
        return _embedding_model
    
    # Load new model
    _embedding_model = SentenceTransformer(model_name)
    _model_name = model_name
    return _embedding_model

def clear_cache():
    """Clear the cached embedding model (useful for testing)"""
    global _embedding_model, _model_name
    _embedding_model = None
    _model_name = None

