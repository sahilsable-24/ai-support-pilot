import uuid 
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.db.models import Document
import logging
from app.ingestion.loaders import load_markdown,load_txt, load_pdf


logger = logging.getLogger(__name__)
ALLOWED_EXTENSIONS = [".pdf",".md",".txt"]
MAX_FILE_SIZE = 20 * 1024 * 1024        #20 MB
STORAGE_DIR = Path("storage/documents")

STORAGE_DIR.mkdir(parents=True,exist_ok=True)

LOADER = {
    ".txt": load_txt,
    ".md": load_markdown,
    ".pdf": load_pdf
}

class InvalidDocumentError(Exception):
    pass

class DocumentNotFoundError(Exception):
    pass

def create_document(db: Session, file: UploadFile) -> Document:

    original_name = file.filename
    extension = Path(original_name).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise InvalidDocumentError(f"Unsupported file type: {extension}")

    contents = file.file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise InvalidDocumentError("File exceeds 20MB Limit")

    doc_id = uuid.uuid4()
    saved_filename = f"{doc_id}{extension}"
    saved_path = STORAGE_DIR / saved_filename

    with open(saved_path,"wb") as f:
        f.write(contents)

    document = Document(
        id = doc_id,
        title = original_name,
        source = saved_filename,
        status = "pending",
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return document


def process_document(db: Session, document_id: uuid.UUID) -> Document:

    document = db.get(Document,document_id)

    if document is None:
        raise DocumentNotFoundError(f"Document {document_id} not found.")

    file_path = STORAGE_DIR / document.source
    extension = file_path.suffix.lower()

    loader = LOADER.get(extension)

    if loader is None:
        document.status = "failed"
        db.commit()
        db.refresh(document)
        raise InvalidDocumentError(f"No loader available for {extension}")

    try:
        pages = loader(file_path)
        total_chars = sum(len(text) for _,text in pages)
        logger.info(f"Extracted {len(pages)} pages, {total_chars} characters from {document.title}")
        document.status = "ready"
    except Exception as e:
        logger.error(f"Failed to process the document {document_id}: {e}")
        document.status = "failed"

    db.commit()
    db.refresh(document)

    return document