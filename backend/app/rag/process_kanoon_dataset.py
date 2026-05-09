"""
Madhyastha — Indian Kanoon Dataset Processor
Processes the Kaggle Indian Kanoon dataset into RAG-ready chunks.
Dataset: https://www.kaggle.com/datasets/regressingaddict/indian-kanoon-cases

Usage:
  1. Download dataset from Kaggle → extract CSV to backend/data/raw/
  2. Run: python -m app.rag.process_kanoon_dataset
"""

import json
import os
import re
import logging
from typing import List, Dict

logger = logging.getLogger("madhyastha.rag.process")

# Dispute type classification keywords
DISPUTE_TYPE_MAP = {
    "property_boundary": ["boundary", "encroachment", "survey", "demarcation", "trespass"],
    "property_ownership": ["title", "ownership", "possession", "partition", "conveyance", "rera", "builder", "flat"],
    "rent_tenancy": ["tenant", "landlord", "rent", "lease", "eviction", "tenancy", "accommodation"],
    "money_loan": ["loan", "debt", "repayment", "recovery", "promissory", "cheque", "dishonour", "138 NI"],
    "contract_breach": ["breach", "contract", "agreement", "service", "vendor", "supply", "performance"],
    "employment": ["employment", "termination", "salary", "wages", "employer", "workman", "gratuity"],
    "consumer": ["consumer", "defective", "product", "service provider", "deficiency", "unfair trade"],
    "family_inheritance": ["inheritance", "succession", "will", "heir", "ancestral", "family property", "HUF"],
    "neighbourhood": ["nuisance", "noise", "pollution", "neighbour", "common area", "society"],
}


def classify_dispute_type(text: str) -> str:
    """Classify dispute type from case text using keyword matching"""
    text_lower = text.lower()
    scores = {}
    for dtype, keywords in DISPUTE_TYPE_MAP.items():
        scores[dtype] = sum(1 for kw in keywords if kw.lower() in text_lower)
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other_civil"


def extract_state(text: str) -> str:
    """Extract Indian state from case text"""
    states = [
        "Karnataka", "Maharashtra", "Delhi", "Tamil Nadu", "Kerala",
        "Gujarat", "Rajasthan", "Uttar Pradesh", "Madhya Pradesh",
        "West Bengal", "Andhra Pradesh", "Telangana", "Punjab",
        "Haryana", "Bihar", "Odisha", "Assam", "Jharkhand", "Chhattisgarh",
        "Uttarakhand", "Himachal Pradesh", "Goa"
    ]
    for state in states:
        if state.lower() in text.lower():
            return state
    # Check court names
    court_state_map = {
        "bombay": "Maharashtra", "madras": "Tamil Nadu", "calcutta": "West Bengal",
        "allahabad": "Uttar Pradesh", "patna": "Bihar", "gauhati": "Assam",
        "karnataka": "Karnataka", "kerala": "Kerala", "gujarat": "Gujarat",
        "rajasthan": "Rajasthan", "punjab": "Punjab", "hyderabad": "Telangana",
        "bengaluru": "Karnataka", "bangalore": "Karnataka", "mumbai": "Maharashtra",
        "chennai": "Tamil Nadu", "kolkata": "West Bengal",
    }
    for key, state in court_state_map.items():
        if key in text.lower():
            return state
    return "India"


def extract_year(text: str) -> int:
    """Extract year from case text"""
    years = re.findall(r'\b(20[0-2]\d)\b', text)
    if years:
        return int(years[-1])
    years = re.findall(r'\b(19[89]\d)\b', text)
    if years:
        return int(years[-1])
    return 2023


def process_kaggle_csv(csv_path: str) -> List[Dict]:
    """Process the Kaggle Indian Kanoon CSV into RAG chunks"""
    import csv

    chunks = []
    with open(csv_path, "r", encoding="utf-8", errors="ignore") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            # The Kaggle dataset typically has columns like:
            # case_title, case_text/doc, court, date, etc.
            title = row.get("title", row.get("case_title", row.get("Title", "")))
            text = row.get("text", row.get("case_text", row.get("doc", row.get("Text", ""))))
            court = row.get("court", row.get("Court", ""))

            if not text or len(text) < 100:
                continue

            # Truncate very long texts to first 2000 chars for summary
            summary_text = text[:2000] if len(text) > 2000 else text

            dispute_type = classify_dispute_type(summary_text)
            state = extract_state(f"{court} {summary_text}")
            year = extract_year(summary_text)

            # Extract key arguments (simple heuristic)
            arguments = []
            arg_patterns = [
                r'held that (.{20,100}?)[\.\n]',
                r'observed that (.{20,100}?)[\.\n]',
                r'the court (.{20,100}?)[\.\n]',
            ]
            for pattern in arg_patterns:
                matches = re.findall(pattern, summary_text, re.IGNORECASE)
                arguments.extend([m.strip() for m in matches[:2]])
            if not arguments:
                arguments = ["Court precedent established"]

            chunk = {
                "case_id": f"IK/{year}/{i + 10000}",
                "dispute_type": dispute_type,
                "summary": (title + ". " if title else "") + summary_text[:500],
                "resolution": "See full judgment",
                "settlement_amount_range": "N/A",
                "resolution_time_days": 0,
                "state": state,
                "year": year,
                "winning_arguments": arguments[:3],
                "court_level": court or "High Court",
                "source": "indian_kanoon_kaggle"
            }
            chunks.append(chunk)

            if i >= 499:  # Limit to 500 cases for RAG performance
                break

    logger.info(f"Processed {len(chunks)} cases from Kaggle CSV")
    return chunks


def merge_with_mock_cases(kaggle_chunks: List[Dict], mock_path: str) -> List[Dict]:
    """Merge Kaggle data with existing mock cases"""
    mock_cases = []
    if os.path.exists(mock_path):
        with open(mock_path, "r", encoding="utf-8") as f:
            mock_cases = json.load(f)
        logger.info(f"Loaded {len(mock_cases)} existing mock cases")

    # Mock cases go first (they have better structured data)
    all_cases = mock_cases + kaggle_chunks
    logger.info(f"Total cases after merge: {len(all_cases)}")
    return all_cases


def process_dataset(csv_path: str = None):
    """Main entry point — process Kaggle dataset and save as RAG chunks"""
    base_dir = os.path.join(os.path.dirname(__file__), "..", "..", "data")
    raw_dir = os.path.join(base_dir, "raw")
    mock_path = os.path.join(raw_dir, "mock_cases.json")

    # Auto-detect CSV in data/raw/
    if not csv_path:
        for fname in os.listdir(raw_dir):
            if fname.endswith(".csv"):
                csv_path = os.path.join(raw_dir, fname)
                logger.info(f"Found CSV: {csv_path}")
                break

    if csv_path and os.path.exists(csv_path):
        kaggle_chunks = process_kaggle_csv(csv_path)
        all_cases = merge_with_mock_cases(kaggle_chunks, mock_path)
    else:
        logger.warning("No Kaggle CSV found. Using mock cases only.")
        logger.info("To use Kaggle data: download from https://www.kaggle.com/datasets/regressingaddict/indian-kanoon-cases")
        logger.info(f"Extract CSV to: {raw_dir}/")
        with open(mock_path, "r", encoding="utf-8") as f:
            all_cases = json.load(f)

    # Save merged chunks
    output_path = os.path.join(raw_dir, "all_cases.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_cases, f, indent=2, ensure_ascii=False)
    logger.info(f"Saved {len(all_cases)} cases to {output_path}")

    # Build FAISS index if available
    try:
        from app.rag.build_index import build_index
        build_index(data_path=output_path)
        logger.info("FAISS index rebuilt successfully")
    except Exception as e:
        logger.warning(f"Could not build FAISS index: {e}")
        # Still save as kanoon_chunks.json for mock retrieval
        chunks_path = os.path.join(base_dir, "kanoon_chunks.json")
        with open(chunks_path, "w", encoding="utf-8") as f:
            json.dump(all_cases, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved chunks to {chunks_path} for mock retrieval")

    return all_cases


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    process_dataset()
