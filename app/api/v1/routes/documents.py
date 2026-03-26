from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.schemas.document import DocumentUploadResponse
from app.services.documents import DocumentService

router = APIRouter(prefix="/documents")


@router.post("/upload", response_model=DocumentUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db_session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> DocumentUploadResponse:
    service = DocumentService(db_session=db_session, settings=settings)
    document = await service.upload(file)

    return DocumentUploadResponse(
        id=document.id,
        filename=document.original_filename,
        content_type=document.content_type,
        file_size=document.file_size,
        ingestion_status=document.ingestion_status,
        created_at=document.created_at,
    )