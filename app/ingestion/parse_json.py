import json
from pathlib import Path
from typing import Dict, Generator

from app.utils.paths import detect_theory_and_book


def iter_documents(json_dir: str) -> Generator[Dict, None, None]:
    base = Path(json_dir)
    for path in base.rglob("*.json"):
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        source_file = data["source_file"]
        theory, book_id = detect_theory_and_book(source_file)
        yield {
            "json_path": path,
            "source_file": source_file,
            "theory": theory,
            "book_id": book_id,
            "total_pages": data.get("total_pages"),
            "pages": data["pages"],
        }
