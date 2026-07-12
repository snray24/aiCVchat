import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.ollama_client import OllamaClient


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, *args, **kwargs):
        self.timeout = kwargs.get("timeout")

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def post(self, url, json=None):
        assert url.endswith("/api/embed")
        return FakeResponse({"embedding": [0.1, 0.2, 0.3]})


class OllamaClientTests(unittest.TestCase):
    def test_embed_supports_single_embedding_payload(self):
        import app.services.ollama_client as ollama_client_module

        ollama_client_module.httpx.AsyncClient = FakeAsyncClient

        client = OllamaClient()
        embedding = asyncio.run(client.embed("hello"))

        self.assertEqual(embedding, [0.1, 0.2, 0.3])


if __name__ == "__main__":
    unittest.main()
