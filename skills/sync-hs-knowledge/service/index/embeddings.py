"""Embedding client supporting LM Studio and local embeddings."""

from typing import List, Optional
import httpx
from service.config import settings


class EmbeddingClient:
    def __init__(
        self,
        provider: str = "lmstudio",
        endpoint: str = "http://10.123.214.1:1234/v1",
        model: str = "text-embedding-nomic-embed-text-v1.5"
    ):
        self.provider = provider
        self.endpoint = endpoint.rstrip("/")
        self.model = model
        self.client = httpx.Client(timeout=10.0)

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Calls LM Studio / OpenAI-compatible embeddings endpoint or returns empty dummy vector on offline/error."""
        if not texts:
            return []

        try:
            url = f"{self.endpoint}/embeddings"
            response = self.client.post(
                url,
                json={"input": texts, "model": self.model}
            )
            if response.status_code == 200:
                data = response.json()
                return [item["embedding"] for item in data.get("data", [])]
        except Exception:
            pass

        # Return placeholder 384-dim zero vectors if server is unreachable
        return [[0.0] * 384 for _ in texts]

    def embed_query(self, query: str) -> List[float]:
        vectors = self.embed_texts([query])
        return vectors[0] if vectors else [0.0] * 384


_global_embedder = None

def get_embedding_client() -> EmbeddingClient:
    global _global_embedder
    if _global_embedder is None:
        _global_embedder = EmbeddingClient(
            provider=settings.embedding_provider,
            endpoint=settings.embedding_endpoint,
            model=settings.embedding_model
        )
    return _global_embedder
