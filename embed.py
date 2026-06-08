"""
Milestone 4 — embed chunks into a vector store and test retrieval.

Pipeline (matches planning.md):
    chunks.json  ->  all-MiniLM-L6-v2 embeddings  ->  ChromaDB  ->  retrieve(query, k=5)

Run:
    python embed.py            # (re)builds the vector store, then runs sample queries

The store is rebuilt from scratch each run so it always matches chunks.json.
"""

import json
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).parent
CHUNKS_PATH = ROOT / "chunks.json"
CHROMA_DIR = ROOT / "chroma_db"
COLLECTION_NAME = "uncc_guide"
EMBED_MODEL = "all-MiniLM-L6-v2"   # from planning.md "Retrieval Approach"
TOP_K = 5                          # from planning.md "Top-k"

# Load the embedding model once and reuse it for both indexing and queries,
# so chunk vectors and query vectors live in the same space.
_model = None


def get_model():
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBED_MODEL} ...")
        _model = SentenceTransformer(EMBED_MODEL)
    return _model


def get_collection():
    """Return the persistent ChromaDB collection (cosine distance)."""
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},   # cosine distance: 0 = identical
    )


def build_vector_store():
    """Embed every chunk in chunks.json and (re)load it into ChromaDB."""
    chunks = json.loads(CHUNKS_PATH.read_text(encoding="utf-8"))
    if not chunks:
        raise SystemExit("chunks.json is empty — run build_chunks.py first.")

    # Rebuild cleanly so the store always reflects the current chunks.json.
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    texts = [c["text"] for c in chunks]
    ids = [c["id"] for c in chunks]
    # Metadata for attribution: source filename + position within that source.
    metadatas = []
    pos = {}
    for c in chunks:
        src = c["source"]
        pos[src] = pos.get(src, 0)
        metadatas.append({"source": src, "position": pos[src]})
        pos[src] += 1

    print(f"Embedding {len(texts)} chunks ...")
    embeddings = get_model().encode(
        texts, batch_size=64, show_progress_bar=True
    ).tolist()

    collection.add(ids=ids, documents=texts,
                   metadatas=metadatas, embeddings=embeddings)
    print(f"Stored {collection.count()} chunks in ChromaDB at {CHROMA_DIR}")
    return collection


def retrieve(query, k=TOP_K, collection=None):
    """Return the top-k chunks most similar to `query`."""
    collection = collection or get_collection()
    q_emb = get_model().encode([query]).tolist()
    res = collection.query(
        query_embeddings=q_emb,
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(res["documents"][0],
                               res["metadatas"][0],
                               res["distances"][0]):
        hits.append({"text": doc, "source": meta["source"], "distance": dist})
    return hits


# Evaluation questions from planning.md (test at least 3 per the milestone).
EVAL_QUESTIONS = [
    "What do students think about Pine Hall?",
    "What concerns do students have about financial aid at UNC Charlotte?",
    "Is there a party scene at UNC Charlotte?",
    "What are the major pros and cons of UNC Charlotte?",
    "How is the social life at UNC Charlotte on weekends?",
]


def test_retrieval(collection):
    for q in EVAL_QUESTIONS:
        print("\n" + "=" * 70)
        print(f"QUERY: {q}")
        print("=" * 70)
        for i, hit in enumerate(retrieve(q, collection=collection), 1):
            preview = hit["text"].replace("\n", " ")
            if len(preview) > 240:
                preview = preview[:240] + "..."
            print(f"\n#{i}  distance={hit['distance']:.3f}  source={hit['source']}")
            print(f"    {preview}")


if __name__ == "__main__":
    collection = build_vector_store()
    test_retrieval(collection)
