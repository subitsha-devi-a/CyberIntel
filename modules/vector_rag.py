
import json
from pathlib import Path

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "threats.json"
)

MODEL_NAME = "all-MiniLM-L6-v2"

_model = None
_documents = None
_embeddings = None
_loaded_mtime = None


def get_model():
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def load_documents():
    global _documents, _embeddings, _loaded_mtime

    if not DATA_FILE.exists():
        return [], None

    current_mtime = DATA_FILE.stat().st_mtime

    # Rebuild the index whenever the JSON file changes.
    if (
        _documents is not None
        and _loaded_mtime == current_mtime
    ):
        return _documents, _embeddings

    with open(DATA_FILE, "r", encoding="utf-8") as file:
        documents = json.load(file)

    model = get_model()

    texts = [
        item.get("title", "") + ". " + item.get("content", "")
        for item in documents
    ]

    if not texts:
        return [], None

    embeddings = model.encode(
        texts,
        convert_to_numpy=True,
        show_progress_bar=False
    )

    _documents = documents
    _embeddings = embeddings
    _loaded_mtime = current_mtime

    return _documents, _embeddings


def reset_vector_index():
    global _documents, _embeddings, _loaded_mtime

    _documents = None
    _embeddings = None
    _loaded_mtime = None


def vector_search(question, top_k=3):

    documents, embeddings = load_documents()

    if not documents or embeddings is None:
        return []

    model = get_model()

    question_embedding = model.encode(
        [question],
        convert_to_numpy=True
    )

    scores = cosine_similarity(
        question_embedding,
        embeddings
    )[0]

    ranked_indices = scores.argsort()[::-1][:top_k]

    results = []

    for index in ranked_indices:

        item = documents[index]

        results.append({
            "title": item.get("title", "Unknown"),
            "content": item.get("content", ""),
            "category": item.get("category", "Unknown"),
            "source": item.get("source", "Unknown"),
            "similarity": float(scores[index]),
            "retrieval_method": "Vector RAG"
        })

    return results
