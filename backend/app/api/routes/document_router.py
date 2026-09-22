from fastapi import APIRouter, HTTPException,Depends,UploadFile
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.document import DocumentResponse
from app.services.document_service import create_document,InvalidDocumentError

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