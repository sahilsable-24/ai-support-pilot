from pathlib import Path


def load_txt(path: Path) -> str:
    return path.read_text(encoding="utf-8")

def load_markdown(path: Path) -> str:
    return path.read_text(encoding="utf-8")