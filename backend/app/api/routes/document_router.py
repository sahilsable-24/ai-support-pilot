from fastapi import APIRouter, HTTPException,Depends,UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.document import DocumentResponse
from app.services.document_service import create_document,InvalidDocumentError, process_document, DocumentNotFoundError, delete_document
from sqlalchemy import select
from app.db.models import Document
import uuid

router = APIRouter(prefix="/documents",tags=["documents"])


@router.post("",response_model=DocumentResponse, status_code=201)
def upload_document(
    file: UploadFile,
    db: Session = Depends(get_db),
):
    try:
        return create_document(db,file)
    except InvalidDocumentError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{document_id}/process", response_model=DocumentResponse)
def process_document_route(
    document_id: uuid.UUID,
    db: Session = Depends(get_db),
):
    try:
        return process_document(db,document_id)
    except DocumentNotFoundError as e:
        return HTTPException(status_code=404, detail=str(e))
    except InvalidDocumentError as e:
        return HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    return db.scalars(select(Document).order_by(Document.created_at.desc())).all()

from app.services.document_service import delete_document


@router.delete("/{document_id}", status_code=204)
def delete_document_route(document_id: uuid.UUID, db: Session = Depends(get_db)):
    try:
        delete_document(db, document_id)
    except DocumentNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))