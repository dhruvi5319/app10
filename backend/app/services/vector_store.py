"""ChromaDB vector store wrapper for per-session embedding collections."""

import logging

import chromadb
from fastapi import HTTPException

from app.config import get_settings
from app.models.errors import ErrorCode

logger = logging.getLogger(__name__)

# Module-level ChromaDB client (initialized lazily)
_chroma_client: chromadb.ClientAPI | None = None


def _get_client() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        settings = get_settings()
        _chroma_client = chromadb.PersistentClient(path=settings.VECTOR_STORE_PATH)
    return _chroma_client


def set_client(client: chromadb.ClientAPI) -> None:
    """Override client — used in tests to inject EphemeralClient."""
    global _chroma_client
    _chroma_client = client


def get_or_create_collection(session_id: str) -> chromadb.Collection:
    """Get or create a per-session ChromaDB collection with cosine distance."""
    client = _get_client()
    collection = client.get_or_create_collection(
        name=f"session_{session_id}",
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def upsert_chunks(
    session_id: str,
    chunk_ids: list[str],
    embeddings: list[list[float]],
    texts: list[str],
    metadatas: list[dict],
) -> None:
    """Upsert chunk embeddings into the session's ChromaDB collection."""
    collection = get_or_create_collection(session_id)

    # ChromaDB cannot store None values in metadata — convert page_number=None → -1
    sanitized_metadatas = []
    for meta in metadatas:
        m = dict(meta)
        if m.get("page_number") is None:
            m["page_number"] = -1
        sanitized_metadatas.append(m)

    collection.upsert(
        ids=chunk_ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=sanitized_metadatas,
    )
    logger.debug(f"Upserted {len(chunk_ids)} chunks to collection session_{session_id}")


def query_chunks(
    session_id: str,
    query_embedding: list[float],
    top_k: int = 5,
) -> list[dict]:
    """
    Query the session collection for similar chunks.
    Returns list of dicts with chunk data; similarity_score = 1 - cosine_distance.
    """
    try:
        collection = get_or_create_collection(session_id)

        # Check collection is non-empty first
        count = collection.count()
        if count == 0:
            return []

        actual_k = min(top_k, count)
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_k,
            include=["documents", "metadatas", "distances"],
        )

        chunks: list[dict] = []
        if not results["ids"] or not results["ids"][0]:
            return chunks

        for i, chunk_id in enumerate(results["ids"][0]):
            distance = results["distances"][0][i]  # type: ignore[index]
            similarity_score = 1.0 - distance  # cosine: distance → similarity
            meta = results["metadatas"][0][i]  # type: ignore[index]
            text = results["documents"][0][i]  # type: ignore[index]

            # Convert page_number -1 back to None
            page_number = meta.get("page_number")
            if page_number == -1:
                page_number = None

            chunks.append(
                {
                    "chunk_id": chunk_id,
                    "text": text,
                    "doc_id": meta.get("doc_id", ""),
                    "filename": meta.get("filename", ""),
                    "page_number": page_number,
                    "chunk_index": meta.get("chunk_index", 0),
                    "similarity_score": similarity_score,
                }
            )

        return chunks

    except Exception as exc:
        logger.error(f"ChromaDB query failed: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.RETRIEVAL_FAILURE,
                "message": f"Vector store query failed: {exc}",
            },
        ) from exc


def delete_doc_chunks(session_id: str, doc_id: str) -> None:
    """Delete all chunks for a given doc_id from the session collection."""
    try:
        collection = get_or_create_collection(session_id)
        collection.delete(where={"doc_id": doc_id})
        logger.debug(f"Deleted chunks for doc_id={doc_id} from session_{session_id}")
    except Exception as exc:
        logger.warning(f"Failed to delete chunks for doc_id={doc_id}: {exc}")
        # Don't raise — deletion is best-effort
