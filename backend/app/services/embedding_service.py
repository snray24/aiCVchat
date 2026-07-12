"""Embedding service for generating and managing embeddings."""
from typing import List
from app.services.ollama_client import ollama_client
from app.core.logging import logger


class EmbeddingService:
    """Service for generating embeddings."""
    
    def __init__(self):
        self.client = ollama_client
    
    async def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        if not text or not text.strip():
            return []
        return await self.client.embed(text)
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            return []
        return await self.client.embed_batch(valid_texts)


embedding_service = EmbeddingService()
