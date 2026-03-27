import hashlib
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.db.models.document import Document
from app.db.models.document_chunk import DocumentChunk
from app.services.embeddings import EmbeddingService
from app.services.ingestion import chunk_text, clean_text, parse_document_bytes


class DocumentService:
    def __init__(self, db_session: Session, settings: Settings) -> None:
        self.db_session = db_session
        self.settings = settings
        self.embedding_service = EmbeddingService(settings=settings)

    async def upload(self, file: UploadFile) -> Document:
        content = await file.read()
        filename = Path(file.filename or "unnamed").name
        content_type = file.content_type or "application/octet-stream"

        self._validate_upload(filename=filename, content_type=content_type, size_bytes=len(content))

        document_id = str(uuid.uuid4())
        extension = Path(filename).suffix
        stored_filename = f"{document_id}{extension}"

        upload_dir = Path(self.settings.storage_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        storage_path = upload_dir / stored_filename
        storage_path.write_bytes(content)

        sha256_hash = hashlib.sha256(content).hexdigest()

        document = Document(
            id=document_id,
            original_filename=filename,
            stored_filename=stored_filename,
            storage_path=str(storage_path),
            content_type=content_type,
            file_size=len(content),
            sha256=sha256_hash,
            ingestion_status="uploaded",
        )

        self.db_session.add(document)
        self.db_session.commit()

        try:
            self._ingest_document_content(document=document, content=content)
            document.ingestion_status = "embedded"
            document.error_message = None
            self.db_session.commit()
        except Exception as exc:
            self.db_session.rollback()
            document.ingestion_status = "failed"
            document.error_message = str(exc)[:1000]
            self.db_session.add(document)
            self.db_session.commit()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Document ingestion failed during parsing/chunking.",
            ) from exc

        self.db_session.refresh(document)

        return document

    def _ingest_document_content(self, document: Document, content: bytes) -> None:
        document.ingestion_status = "processing"
        self.db_session.add(document)
        self.db_session.commit()

        parsed_text = parse_document_bytes(content=content, content_type=document.content_type)
        cleaned_text = clean_text(parsed_text)

        extracted_chunks = chunk_text(
            text=cleaned_text,
            chunk_size=self.settings.chunk_size_chars,
            overlap=self.settings.chunk_overlap_chars,
        )

        if not extracted_chunks:
            raise ValueError("No chunks were produced from document content.")

        for parsed_chunk in extracted_chunks:
            self.db_session.add(
                DocumentChunk(
                    document_id=document.id,
                    chunk_index=parsed_chunk.chunk_index,
                    content=parsed_chunk.text,
                    char_start=parsed_chunk.char_start,
                    char_end=parsed_chunk.char_end,
                    token_estimate=max(1, len(parsed_chunk.text) // 4),
                )
            )

        self.db_session.commit()

        persisted_chunks = (
            self.db_session.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document.id)
            .order_by(DocumentChunk.chunk_index.asc())
            .all()
        )

        embeddings = self.embedding_service.embed_many(
            [persisted_chunk.content for persisted_chunk in persisted_chunks]
        )

        for persisted_chunk, embedding in zip(persisted_chunks, embeddings, strict=False):
            persisted_chunk.embedding = embedding

        self.db_session.add_all(persisted_chunks)
        self.db_session.commit()

    def _validate_upload(self, filename: str, content_type: str, size_bytes: int) -> None:
        if size_bytes == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded file is empty.",
            )

        if size_bytes > self.settings.max_upload_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds max size of {self.settings.max_upload_size_bytes} bytes.",
            )

        allowed_types = {
            value.strip()
            for value in self.settings.allowed_upload_content_types.split(",")
            if value.strip()
        }

        if content_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=(
                    f"Unsupported content type '{content_type}'. "
                    f"Allowed types: {sorted(allowed_types)}"
                ),
            )

        extension = Path(filename).suffix.lower()
        if content_type == "application/pdf" and extension != ".pdf":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="PDF uploads must use a .pdf extension.",
            )

        if content_type == "text/plain" and extension not in {".txt", ".md"}:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Plain text uploads must use .txt or .md extension.",
            )