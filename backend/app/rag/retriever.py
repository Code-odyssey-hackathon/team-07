"""
Madhyastha — RAG Retriever
FAISS-based legal precedent retrieval with MMR diversity
"""

import json
import os
import logging
from typing import List, Dict, Optional
import numpy as np

logger = logging.getLogger("madhyastha.rag.retriever")

# Try to import faiss
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not installed. Using mock retrieval.")


class LegalRetriever:
    """Retrieves relevant legal precedents from FAISS index"""

    def __init__(self, index_path: str = None, chunks_path: str = None):
        self.index = None
        self.chunks = []
        self.index_path = index_path or "data/kanoon_faiss.index"
        self.chunks_path = chunks_path or "data/kanoon_chunks.json"

        self._load_index()

    def _load_index(self):
        """Load FAISS index and chunks from disk"""
        if not FAISS_AVAILABLE:
            logger.info("FAISS not available, loading mock cases")
            self._load_mock_cases()
            return

        if os.path.exists(self.index_path) and os.path.exists(self.chunks_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.chunks_path, "r", encoding="utf-8") as f:
                    self.chunks = json.load(f)
                logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
            except Exception as e:
                logger.error(f"Failed to load FAISS index: {e}")
                self._load_mock_cases()
        else:
            logger.info("FAISS index not found, using mock cases")
            self._load_mock_cases()

    def _load_mock_cases(self):
        """Load cases for demo mode — prefers merged dataset if available"""
        base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
        # Try merged dataset first (Kaggle + mock)
        all_path = os.path.join(base_dir, "raw", "all_cases.json")
        mock_path = os.path.join(base_dir, "raw", "mock_cases.json")
        chunks_path = os.path.join(base_dir, "kanoon_chunks.json")

        for path in [chunks_path, all_path, mock_path]:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        self.chunks = json.load(f)
                    logger.info(f"Loaded {len(self.chunks)} cases from {os.path.basename(path)}")
                    return
                except Exception as e:
                    logger.error(f"Failed to load {path}: {e}")

        self.chunks = self._builtin_mock_cases()

    def get_precedents(
        self,
        query: str,
        top_k: int = 5,
        dispute_type: Optional[str] = None,
    ) -> List[Dict]:
        """Retrieve top-k relevant legal precedents"""
        if self.index and FAISS_AVAILABLE:
            return self._faiss_search(query, top_k, dispute_type)
        else:
            return self._mock_search(query, top_k, dispute_type)

    def _faiss_search(self, query: str, top_k: int, dispute_type: Optional[str]) -> List[Dict]:
        """FAISS-based semantic search"""
        from app.rag.embedder import embedder

        query_vector = embedder.embed(query).reshape(1, -1)
        distances, indices = self.index.search(query_vector, top_k * 2)

        results = []
        for idx in indices[0]:
            if idx < len(self.chunks) and idx >= 0:
                chunk = self.chunks[idx]
                if dispute_type and chunk.get("dispute_type") != dispute_type:
                    continue
                results.append(chunk)
                if len(results) >= top_k:
                    break

        # If filtering removed too many, add without filter
        if len(results) < top_k:
            for idx in indices[0]:
                if idx < len(self.chunks) and idx >= 0:
                    chunk = self.chunks[idx]
                    if chunk not in results:
                        results.append(chunk)
                        if len(results) >= top_k:
                            break

        return results

    def _mock_search(self, query: str, top_k: int, dispute_type: Optional[str]) -> List[Dict]:
        """Mock search based on keyword matching"""
        scored = []
        query_lower = query.lower()

        for chunk in self.chunks:
            score = 0
            text = (chunk.get("summary", "") + " " + chunk.get("dispute_type", "")).lower()

            # Type matching
            if dispute_type and chunk.get("dispute_type") == dispute_type:
                score += 10

            # Keyword matching
            for word in query_lower.split():
                if word in text:
                    score += 1

            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item[1] for item in scored[:top_k]]

    def _builtin_mock_cases(self) -> List[Dict]:
        """Built-in mock cases when no data files exist"""
        return [
            {
                "case_id": "IK/2022/45621",
                "dispute_type": "money_loan",
                "summary": "Loan dispute between business partners. Borrower unable to repay full amount due to business failure. Mediated settlement at 70% with 18-month installment plan.",
                "resolution": "Partial payment of 70% in installments",
                "settlement_amount_range": "1-5 lakhs",
                "resolution_time_days": 45,
                "state": "Karnataka",
                "year": 2022,
                "winning_arguments": ["Business failure as mitigating factor", "Good faith partial offer"],
                "court_level": "Lok Adalat"
            },
            {
                "case_id": "IK/2023/12890",
                "dispute_type": "property_boundary",
                "summary": "Boundary dispute between neighbors. Survey conducted, compromise on shared access pathway. Registered boundary agreement.",
                "resolution": "Shared access with registered boundary",
                "settlement_amount_range": "N/A",
                "resolution_time_days": 60,
                "state": "Maharashtra",
                "year": 2023,
                "winning_arguments": ["Survey evidence", "Historical usage rights"],
                "court_level": "Mediation Centre"
            },
            {
                "case_id": "IK/2021/78432",
                "dispute_type": "rent_tenancy",
                "summary": "Tenant refused to vacate after lease expiry. Landlord sought eviction plus damages. Settled with 3-month extension and repair compensation.",
                "resolution": "Tenant vacated with 3-month extension, ₹50,000 repair compensation",
                "settlement_amount_range": "50,000-1 lakh",
                "resolution_time_days": 30,
                "state": "Delhi",
                "year": 2021,
                "winning_arguments": ["Lease terms clear", "Tenant hardship considered"],
                "court_level": "Rent Controller"
            },
            {
                "case_id": "CF/2023/5543",
                "dispute_type": "consumer",
                "summary": "Consumer complaint about defective electronic product. Manufacturer offered replacement but consumer sought refund. Settled with full refund plus compensation.",
                "resolution": "Full refund + ₹10,000 compensation",
                "settlement_amount_range": "10,000-50,000",
                "resolution_time_days": 21,
                "state": "Tamil Nadu",
                "year": 2023,
                "winning_arguments": ["Product defect proven", "Consumer Protection Act provisions"],
                "court_level": "Consumer Forum"
            },
            {
                "case_id": "IK/2022/33201",
                "dispute_type": "contract_breach",
                "summary": "Service contract breach. Provider failed to deliver as per timeline. Client sought damages. Settled at 50% refund with completion guarantee.",
                "resolution": "50% refund + completion within 30 days",
                "settlement_amount_range": "1-3 lakhs",
                "resolution_time_days": 35,
                "state": "Gujarat",
                "year": 2022,
                "winning_arguments": ["Contract terms clear", "Partial performance acknowledged"],
                "court_level": "Lok Adalat"
            }
        ]


# Global instance
retriever = LegalRetriever()
