from io import BytesIO

from pypdf import PdfReader


def parse_document_bytes(content: bytes, content_type: str) -> str:
    if content_type == "text/plain":
        return content.decode("utf-8", errors="ignore")

    if content_type == "application/pdf":
        return _parse_pdf(content)

    raise ValueError(f"Unsupported content type for parser: {content_type}")


def _parse_pdf(content: bytes) -> str:
    reader = PdfReader(BytesIO(content))
    page_text: list[str] = []

    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            page_text.append(extracted)

    return "\n\n".join(page_text)
