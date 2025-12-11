import uuid


def make_chunk_id(text: str) -> str:
    """
    Deterministic UUIDv5 from text, valid for Qdrant point ids.
    """
    return str(uuid.uuid5(uuid.NAMESPACE_URL, text))
