"""
Madhyastha — RAG Embedder
Sentence-transformers embedding for legal precedent retrieval
"""

import logging
from typing import List
import numpy as np

logger = logging.getLogger("madhyastha.rag.embedder")

# Try to import sentence-transformers
try:
    from sentence_transformers import SentenceTransformer
    ST_AVAILABLE = True
except ImportError:
    ST_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Using mock embeddings.")


class LegalEmbedder:
    """Embeds legal text using multilingual sentence-transformers"""

    MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

    def __init__(self):
        self.model = None
        if ST_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.MODEL_NAME)
                logger.info(f"Loaded embedding model: {self.MODEL_NAME}")
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")

    def embed(self, text: str) -> np.ndarray:
        """Embed a single text string"""
        if self.model:
            return self.model.encode(text, normalize_embeddings=True)
        else:
            # Mock embedding — random 384-dim vector (MiniLM output dim)
            return np.random.rand(384).astype(np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """Embed a batch of texts"""
        if self.model:
            return self.model.encode(texts, normalize_embeddings=True, show_progress_bar=True)
        else:
            return np.random.rand(len(texts), 384).astype(np.float32)

    @property
    def dimension(self) -> int:
        return 384


# Global instance
embedder = LegalEmbedder()
