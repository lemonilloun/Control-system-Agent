from pathlib import Path


def detect_theory_and_book(source_file: str) -> tuple[str, str]:
    """
    Maps source file name to theory/book id.
    NL-Khalil-11-40.pdf / DС-Ogata-... / CLS-Ogata-...
    """
    name = Path(source_file).name
    prefix = name.split("-")[0].upper()
    if prefix.startswith("NL"):
        return "nonlinear", "nl_khalil"
    if prefix.startswith("DC") or prefix.startswith("DС"):  # cover Cyrillic С
        return "discrete", "ds_ogata"
    return "linear", "cls_ogata"
