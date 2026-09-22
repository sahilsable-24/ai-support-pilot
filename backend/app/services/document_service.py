import uuid 
from pathlib import Path
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.db.models import Document


ALLOWED_EXTENSIONS = [".pdf",".md",".txt"]
MAX_FILE_SIZE = 20 * 1024 * 1024        #20 MB
STORAGE_DIR = Path("storage/documents")

STORAGE_DIR.mkdir(parents=True,exist_ok=True)

class InvalidDocumentError(Exception):
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