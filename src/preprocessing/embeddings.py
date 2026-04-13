"""
embeddings.py — Generate embeddings for MDM records and use FAISS
to find candidate pairs for matching (avoids O(n²) brute force).

Strategy:
    Format each record as a structured string, encode with sentence-transformers,
    index with FAISS, then pull the top-k nearest neighbors for each record.
    Any pair with cosine similarity > SIMILARITY_THRESHOLD becomes a candidate.
"""

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from src.utils.config import EMBEDDING_MODEL, EMBEDDING_FIELD_FORMAT, SIMILARITY_THRESHOLD
from src.utils.logger import get_logger

logger = get_logger(__name__)

# Load model once at module level so we're not reloading it every call
_model = None

def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info(f"Loading embedding model: {EMBEDDING_MODEL}")
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def format_record_for_embedding(record: dict) -> str:
    """
    Format a record into the structured string we'll embed.
    Uses the expanded/translated fields if available, falls back to cleaned.

    Output looks like:
        "company: boeing || address: 100 north riverside plaza || city: chicago || country: usa"
    """
    name = record.get("name_expanded") or record.get("name_translated") or record.get("name_clean", "")
    address = record.get("address_expanded") or record.get("address_translated") or record.get("address_clean", "")
    city = record.get("city_translated") or record.get("city_clean", "")
    country = record.get("country_clean", "")

    return EMBEDDING_FIELD_FORMAT.format(
        name=name,
        address=address,
        city=city,
        country=country,
    )


def generate_embeddings(records: list[dict]) -> np.ndarray:
    """
    Generate embeddings for a list of processed records.
    Returns a float32 numpy array of shape (n_records, embedding_dim).
    """
    model = get_model()
    texts = [format_record_for_embedding(r) for r in records]

    logger.info(f"Generating embeddings for {len(texts)} records...")
    embeddings = model.encode(texts, show_progress_bar=True, convert_to_numpy=True)
    embeddings = embeddings.astype(np.float32)

    # Normalize for cosine similarity (FAISS inner product on normalized = cosine)
    faiss.normalize_L2(embeddings)
    return embeddings


def build_faiss_index(embeddings: np.ndarray) -> faiss.IndexFlatIP:
    """
    Build a FAISS flat inner product index from embeddings.
    Since vectors are normalized, inner product == cosine similarity.
    """
    dim = embeddings.shape[1]
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings)
    logger.info(f"FAISS index built with {index.ntotal} vectors (dim={dim})")
    return index


def find_candidate_pairs(
    records: list[dict],
    embeddings: np.ndarray,
    index: faiss.IndexFlatIP,
    top_k: int = 10,
    threshold: float = SIMILARITY_THRESHOLD,
) -> list[tuple[int, int, float]]:
    """
    For each record, find its top-k nearest neighbors and return pairs
    where similarity >= threshold.

    Returns a list of (idx_a, idx_b, similarity_score) tuples, deduplicated
    so we don't return both (a, b) and (b, a).
    """
    logger.info(f"Finding candidate pairs (top_k={top_k}, threshold={threshold})...")

    similarities, indices = index.search(embeddings, top_k + 1)  # +1 because record matches itself

    candidate_pairs = set()
    for i in range(len(records)):
        for rank in range(1, top_k + 1):   # skip rank 0 (self)
            j = indices[i][rank]
            sim = similarities[i][rank]

            if j == -1 or sim < threshold:
                continue

            # Dedup: always store with smaller index first
            pair = (min(i, j), max(i, j))
            if pair not in candidate_pairs:
                candidate_pairs.add((pair[0], pair[1], float(sim)))

    result = sorted(candidate_pairs, key=lambda x: x[2], reverse=True)
    logger.info(f"Found {len(result)} candidate pairs above threshold {threshold}")
    return result


def run_embedding_pipeline(records: list[dict]) -> tuple[np.ndarray, faiss.IndexFlatIP, list]:
    """
    Full embedding pipeline: generate → index → find pairs.
    Returns (embeddings, index, candidate_pairs).
    """
    embeddings = generate_embeddings(records)
    index = build_faiss_index(embeddings)
    pairs = find_candidate_pairs(records, embeddings, index)
    return embeddings, index, pairs


if __name__ == "__main__":
    # Quick test with dummy records
    dummy_records = [
        {"name_clean": "boeing", "address_clean": "100 north riverside", "city_clean": "chicago", "country_clean": "usa"},
        {"name_clean": "the boeing company", "address_clean": "100 n riverside plaza", "city_clean": "chicago", "country_clean": "united states"},
        {"name_clean": "airbus", "address_clean": "1 rond-point maurice bellonte", "city_clean": "toulouse", "country_clean": "france"},
        {"name_clean": "lockheed martin", "address_clean": "6801 rockledge dr", "city_clean": "bethesda", "country_clean": "usa"},
        {"name_clean": "lockheed martin corp", "address_clean": "6801 rockledge drive", "city_clean": "bethesda", "country_clean": "us"},
    ]

    embs, idx, pairs = run_embedding_pipeline(dummy_records)
    print(f"\nCandidate pairs found: {len(pairs)}")
    for a, b, sim in pairs:
        print(f"  [{a}] {dummy_records[a]['name_clean']!r:30} ↔ [{b}] {dummy_records[b]['name_clean']!r:30}  sim={sim:.3f}")
