from app.services.ingestion.chunker import chunk_text
from app.services.ingestion.cleaner import clean_text
from app.services.ingestion.parser import parse_document_bytes


def test_parse_plain_text_bytes() -> None:
    content = b"Hello\nRAG"
    assert parse_document_bytes(content=content, content_type="text/plain") == "Hello\nRAG"


def test_clean_text_normalizes_whitespace() -> None:
    raw = "Line 1\r\n\r\n\r\nLine   2\t\twith spaces"
    cleaned = clean_text(raw)
    assert cleaned == "Line 1\n\nLine 2 with spaces"


def test_chunk_text_produces_overlap_chunks() -> None:
    text = "A" * 2200
    chunks = chunk_text(text=text, chunk_size=1000, overlap=100)

    assert len(chunks) >= 2
    assert chunks[0].char_start == 0
    assert chunks[1].char_start <= chunks[0].char_end
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1
