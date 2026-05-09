"""
Madhyastha — RAG Index Builder
Builds FAISS index from legal case data
"""

import json
import os
import logging
import numpy as np

logger = logging.getLogger("madhyastha.rag.build")


def build_index(data_path: str = None, output_dir: str = None):
    """Build FAISS index from mock/real case data"""
    try:
        import faiss
    except ImportError:
        logger.error("FAISS not installed. Run: pip install faiss-cpu")
        return

    from app.rag.embedder import embedder

    if not data_path:
        base_raw = os.path.join(os.path.dirname(__file__), "..", "..", "data", "raw")
        all_path = os.path.join(base_raw, "all_cases.json")
        mock_path = os.path.join(base_raw, "mock_cases.json")
        data_path = all_path if os.path.exists(all_path) else mock_path
    if not output_dir:
        output_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")

    # Load cases
    with open(data_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    logger.info(f"Building index from {len(cases)} cases...")

    # Create embeddings
    texts = [
        f"{c.get('dispute_type', '')} {c.get('summary', '')} {' '.join(c.get('winning_arguments', []))}"
        for c in cases
    ]
    embeddings = embedder.embed_batch(texts)

    # Build FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatIP(dimension)  # Inner product (cosine with normalized vectors)
    index.add(embeddings.astype(np.float32))

    # Save
    os.makedirs(output_dir, exist_ok=True)
    index_path = os.path.join(output_dir, "kanoon_faiss.index")
    chunks_path = os.path.join(output_dir, "kanoon_chunks.json")

    faiss.write_index(index, index_path)
    with open(chunks_path, "w", encoding="utf-8") as f:
        json.dump(cases, f, indent=2, ensure_ascii=False)

    logger.info(f"Index saved: {index_path} ({index.ntotal} vectors)")
    logger.info(f"Chunks saved: {chunks_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    build_index()
