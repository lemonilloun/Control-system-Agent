from typing import Dict, List


def build_chunks_from_pages(doc: Dict) -> List[Dict]:
    """
    Make one chunk per page (ordered by reading_order).
    """
    chunks = []
    pages = sorted(doc["pages"], key=lambda p: p["page_number"])
    for page in pages:
        page_no = page["page_number"]
        elements = sorted(page["elements"], key=lambda e: e.get("reading_order", 0))

        texts = [el["text"] for el in elements if el.get("text")]
        if not texts:
            continue

        text = "\n".join(texts)
        chunks.append(
            {
                "text": text,
                "page_start": page_no,
                "page_end": page_no,
                "meta": {
                    "source_file": doc["source_file"],
                    "json_path": str(doc["json_path"]),
                    "book_id": doc["book_id"],
                    "theory": doc["theory"],
                },
            }
        )
    return chunks
