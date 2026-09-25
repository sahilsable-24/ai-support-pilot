from pathlib import Path
from pypdf import PdfReader
import logging

logger = logging.getLogger(__name__)


def load_txt(path: Path) -> list[tuple[int,str]]:
    text = path.read_text(encoding="utf-8")
    return [(1,text)]

def load_markdown(path: Path) -> list[tuple[int,str]]:
    text = path.read_text(encoding="utf-8")
    return [(1,text)]

def load_pdf(path:Path) -> list[tuple[int,str]]:
    reader = PdfReader(path)
    pages = []

    for i,page in enumerate(reader.pages,start=1):
        text = page.extract_text() or ""

        if not text.strip():
            logger.warning(f"Page {i} of {path.name} extracted empty (likely scanned/image)")
            continue

        pages.append((i,text))

    return pages