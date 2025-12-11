from pathlib import Path
from typing import List

from qdrant_client.http.models import Distance, VectorParams, PointStruct
from qdrant_client.http.exceptions import UnexpectedResponse

from app.config import settings
from app.clients.ollama_client import get_embedding_model
from app.clients.qdrant_client import get_qdrant
from app.clients.redis_client import get_redis
from app.ingestion.parse_json import iter_documents
from app.ingestion.chunking import build_chunks_from_pages
from app.utils.hashing import make_chunk_id


def _collection_exists(client, name: str) -> bool:
    try:
        return client.collection_exists(name)
    except AttributeError:
        try:
            client.get_collection(name)
            return True
        except UnexpectedResponse:
            return False


def ensure_collections(embedder) -> None:
    client = get_qdrant()
    try:
        dim = len(embedder.embed_query("dimension_probe"))
    except Exception as exc:
        raise RuntimeError(
            "Embedding model is not available in Ollama. "
            "Pull it first: `ollama pull ${OLLAMA_EMBED_MODEL_NAME}` "
            f"(current: {settings.OLLAMA_EMBED_MODEL_NAME}). Original error: {exc}"
        )
    for name in (
        settings.QDRANT_COLLECTION_CLS,
        settings.QDRANT_COLLECTION_DS,
        settings.QDRANT_COLLECTION_NL,
    ):
        if not _collection_exists(client, name):
            client.recreate_collection(
                collection_name=name,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )


def ingest() -> None:
    qdrant = get_qdrant()
    embedder = get_embedding_model()
    redis_client = get_redis()

    ensure_collections(embedder)

    chunks_dir = Path(settings.CHUNKS_DIR)
    chunks_dir.mkdir(parents=True, exist_ok=True)

    for doc in iter_documents(settings.JSON_INPUT_DIR):
        chunks = build_chunks_from_pages(doc)
        if not chunks:
            continue

        texts = [c["text"] for c in chunks]
        vectors = embedder.embed_documents(texts)

        collection = {
            "linear": settings.QDRANT_COLLECTION_CLS,
            "discrete": settings.QDRANT_COLLECTION_DS,
            "nonlinear": settings.QDRANT_COLLECTION_NL,
        }[doc["theory"]]

        points: List[PointStruct] = []
        for chunk, vector in zip(chunks, vectors):
            chunk_id = make_chunk_id(
                f"{doc['source_file']}:{chunk['page_start']}:{chunk['page_end']}"
            )
            txt_path = chunks_dir / f"{chunk_id}.txt"
            txt_path.write_text(chunk["text"], encoding="utf-8")

            payload = {
                "chunk_id": chunk_id,
                "source_file": chunk["meta"]["source_file"],
                "book_id": chunk["meta"]["book_id"],
                "theory": chunk["meta"]["theory"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
            }

            points.append(
                PointStruct(
                    id=chunk_id,
                    vector=vector,
                    payload=payload,
                )
            )

            redis_client.hset(
                f"chunk:{chunk_id}",
                mapping={
                    "path": str(txt_path),
                    "book_id": payload["book_id"],
                    "theory": payload["theory"],
                },
            )

        if points:
            qdrant.upsert(collection_name=collection, points=points)
            print(f"Ingested {len(points)} chunks into {collection} from {doc['source_file']}")


if __name__ == "__main__":
    ingest()
