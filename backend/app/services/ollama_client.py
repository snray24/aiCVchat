"""Ollama HTTP client for chat and embeddings."""
import httpx
from typing import List, Any
from app.core.config import settings
from app.core.logging import logger


class OllamaClient:
    """Client for Ollama API."""
    
    def __init__(self):
        self.base_url = settings.ollama_base_url
        self.chat_model = settings.ollama_chat_model
        self.embed_model = settings.ollama_embed_model
        self.timeout = 120.0  # 2 minutes for CPU inference

    def _extract_embedding(self, data: dict[str, Any]) -> List[float]:
        """Normalize embedding payloads from different Ollama response shapes."""
        if not isinstance(data, dict):
            return []

        if isinstance(data.get("embedding"), list):
            return [float(value) for value in data["embedding"]]

        embeddings = data.get("embeddings")
        if isinstance(embeddings, list):
            if embeddings and isinstance(embeddings[0], list):
                return [float(value) for value in embeddings[0]]
            if embeddings and all(isinstance(value, (int, float)) for value in embeddings):
                return [float(value) for value in embeddings]

        logger.warning(f"Unexpected Ollama embedding payload: {data}")
        return []
    
    async def chat(self, messages: List[dict[str, str]], stream: bool = False) -> str:
        """Send chat completion request to Ollama."""
        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.chat_model,
            "messages": messages,
            "stream": stream
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("message", {}).get("content", "")
            except httpx.HTTPError as e:
                logger.error(f"Ollama chat error: {e}")
                raise
    
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for text using Ollama."""
        url = f"{self.base_url}/api/embed"
        payload = {
            "model": self.embed_model,
            "input": text
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                logger.info(f"Ollama embed response: {data.keys()}")
                embedding = self._extract_embedding(data)
                if not embedding:
                    raise ValueError(f"Ollama returned no embedding payload: {data}")
                return embedding
            except httpx.HTTPError as e:
                logger.error(f"Ollama embed error: {e}")
                logger.error(f"Request payload: {payload}")
                raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = []
        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)
        return embeddings


ollama_client = OllamaClient()
