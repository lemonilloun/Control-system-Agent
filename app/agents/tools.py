from typing import Dict, List
import json
import logging

import httpx
from langchain_core.tools import tool

from app.clients.qdrant_client import get_qdrant
from app.clients.redis_client import get_redis
from app.clients.ollama_client import get_embedding_model
from app.config import settings

log = logging.getLogger(__name__)


def _search_collection(collection: str, query: str, k: int = 5) -> List[Dict]:
    _ = get_qdrant()  # keep client around in case of future use/reuse
    embedder = get_embedding_model()
    redis_client = get_redis()

    vector = embedder.embed_query(query)
    log.info(f"[search] collection={collection} q='{query}' k={k}")

    base = settings.QDRANT_URL.rstrip("/")
    url = f"{base}/collections/{collection}/points/search"
    payload = {"vector": vector, "limit": k}

    try:
        resp = httpx.post(url, json=payload, timeout=600.0)  # allow up to 10 minutes
        resp.raise_for_status()
        data = resp.json()
        search_result = data.get("result") or []
    except Exception as exc:
        log.error(f"[search] REST search failed for {collection}: {exc}")
        raise

    chunks = []
    for point in search_result:
        pid = str(point.get("id"))
        meta = point.get("payload") or {}
        score = point.get("score")

        redis_meta = redis_client.hgetall(f"chunk:{pid}")
        path = redis_meta.get("path")
        text = ""
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    text = f.read()
            except FileNotFoundError:
                text = ""

        chunks.append(
            {
                "chunk_id": pid,
                "text": text,
                "score": score,
                "book_id": meta.get("book_id"),
                "theory": meta.get("theory"),
                "page_start": meta.get("page_start"),
                "page_end": meta.get("page_end"),
            }
        )
    log.info(f"[search] found {len(chunks)} chunks in {collection}")
    return chunks


@tool("translate_to_russian", return_direct=True)
def translate_to_russian(text: str) -> str:
    """
    Переводит произвольный текст на русский язык, сохраняя смысл и математические обозначения.
    """
    base = settings.OLLAMA_BASE_URL.rstrip("/")
    url = f"{base}/api/chat"
    payload = {
        "model": settings.OLLAMA_MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Переведи текст на русский, кратко и ясно. Оставь математические обозначения без изменений. Ответь только переводом."},
            {"role": "user", "content": text},
        ],
        "stream": False,
    }
    try:
        resp = httpx.post(url, json=payload, timeout=120.0)
        resp.raise_for_status()
        data = resp.json()
        message = data.get("message", {}) if isinstance(data, dict) else {}
        content = message.get("content") or ""
        if not content and isinstance(data, dict):
            content = data.get("response") or ""
        return content or text
    except Exception as exc:
        log.error(f"[translate] failed to translate: {exc}")
        return text


@tool("search_cls_ogata", return_direct=False)
def search_cls_ogata(query: str) -> List[Dict]:
    """Поиск по книге Katsuhiko Ogata (классические линейные системы управления)."""
    return _search_collection(settings.QDRANT_COLLECTION_CLS, query)


@tool("search_ds_ogata", return_direct=False)
def search_ds_ogata(query: str) -> List[Dict]:
    """Поиск по книге Ogata 'Discrete-Time Control Systems'."""
    return _search_collection(settings.QDRANT_COLLECTION_DS, query)


@tool("search_nl_khalil", return_direct=False)
def search_nl_khalil(query: str) -> List[Dict]:
    """Поиск по книге Khalil 'Nonlinear Systems'."""
    return _search_collection(settings.QDRANT_COLLECTION_NL, query)


TOOLS = [search_cls_ogata, search_ds_ogata, search_nl_khalil, translate_to_russian]
