from collections.abc import Callable, Generator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
from app.db.models.document_chunk import DocumentChunk
from app.db.session import get_db_session
from app.main import app


def _override_db_session_factory(
    database_url: str,
) -> tuple[Callable[[], Generator[Session, None, None]], sessionmaker[Session]]:
    engine = create_engine(database_url)
    testing_session_local = sessionmaker(bind=engine, autocommit=False, autoflush=False)
    Base.metadata.create_all(bind=engine)

    def _override_get_db_session() -> Generator[Session, None, None]:
        session = testing_session_local()
        try:
            yield session
        finally:
            session.close()

    return _override_get_db_session, testing_session_local


def test_upload_text_document(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    upload_dir = tmp_path / "uploads"
    sqlite_db_path = tmp_path / "test.db"
    database_url = f"sqlite+pysqlite:///{sqlite_db_path}"

    monkeypatch.setenv("STORAGE_DIR", str(upload_dir))
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    override_dependency, testing_session_local = _override_db_session_factory(database_url)
    app.dependency_overrides[get_db_session] = override_dependency
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("notes.txt", b"RAG systems retrieve context.", "text/plain")},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["filename"] == "notes.txt"
    assert data["content_type"] == "text/plain"
    assert data["file_size"] > 0
    assert data["ingestion_status"] == "embedded"
    assert data["chunk_count"] > 0

    stored_files = list(upload_dir.glob("*"))
    assert len(stored_files) == 1
    assert stored_files[0].read_bytes() == b"RAG systems retrieve context."

    session = testing_session_local()
    try:
        persisted_chunks = session.query(DocumentChunk).all()
        assert len(persisted_chunks) == data["chunk_count"]
        assert all(chunk.embedding is not None for chunk in persisted_chunks)
    finally:
        session.close()

    app.dependency_overrides.clear()
    get_settings.cache_clear()


def test_reject_unsupported_content_type(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    sqlite_db_path = tmp_path / "test.db"
    database_url = f"sqlite+pysqlite:///{sqlite_db_path}"

    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    override_dependency, _ = _override_db_session_factory(database_url)
    app.dependency_overrides[get_db_session] = override_dependency
    client = TestClient(app)

    response = client.post(
        "/api/v1/documents/upload",
        files={"file": ("malicious.exe", b"binary", "application/octet-stream")},
    )

    assert response.status_code == 415
    assert "Unsupported content type" in response.json()["detail"]

    app.dependency_overrides.clear()
    get_settings.cache_clear()