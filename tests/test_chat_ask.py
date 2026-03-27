from collections.abc import Callable, Generator
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db.base import Base
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


def test_chat_ask_returns_citations(tmp_path: Path, monkeypatch: MonkeyPatch) -> None:
    upload_dir = tmp_path / "uploads"
    sqlite_db_path = tmp_path / "test.db"
    database_url = f"sqlite+pysqlite:///{sqlite_db_path}"

    monkeypatch.setenv("STORAGE_DIR", str(upload_dir))
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("EMBEDDING_PROVIDER", "local")
    monkeypatch.setenv("LLM_PROVIDER", "local")
    get_settings.cache_clear()

    override_dependency, _ = _override_db_session_factory(database_url)
    app.dependency_overrides[get_db_session] = override_dependency
    client = TestClient(app)

    upload_response = client.post(
        "/api/v1/documents/upload",
        files={
            "file": (
                "rag_notes.txt",
                b"FastAPI is an async web framework. pgvector enables vector similarity search.",
                "text/plain",
            )
        },
    )
    assert upload_response.status_code == 201

    ask_response = client.post(
        "/api/v1/chat/ask",
        json={"question": "What enables vector similarity search?", "top_k": 3},
    )

    assert ask_response.status_code == 200
    data = ask_response.json()
    assert isinstance(data["answer"], str)
    assert len(data["answer"]) > 0
    assert len(data["citations"]) > 0
    assert "document_id" in data["citations"][0]
    assert "chunk_id" in data["citations"][0]
    assert "score" in data["citations"][0]

    app.dependency_overrides.clear()
    get_settings.cache_clear()
