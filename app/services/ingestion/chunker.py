from dataclasses import dataclass


@dataclass(slots=True)
class TextChunk:
    chunk_index: int
    text: str
    char_start: int
    char_end: int


def chunk_text(text: str, chunk_size: int, overlap: int) -> list[TextChunk]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be > 0")

    if overlap < 0:
        raise ValueError("overlap must be >= 0")

    if overlap >= chunk_size:
        raise ValueError("overlap must be smaller than chunk_size")

    if not text.strip():
        return []

    chunks: list[TextChunk] = []
    cursor = 0
    chunk_index = 0
    text_length = len(text)

    while cursor < text_length:
        max_end = min(cursor + chunk_size, text_length)
        end = _find_chunk_breakpoint(text=text, start=cursor, max_end=max_end)

        if end <= cursor:
            end = max_end

        chunk_text_value = text[cursor:end].strip()
        if chunk_text_value:
            chunks.append(
                TextChunk(
                    chunk_index=chunk_index,
                    text=chunk_text_value,
                    char_start=cursor,
                    char_end=end,
                )
            )
            chunk_index += 1

        if end == text_length:
            break

        cursor = max(end - overlap, cursor + 1)

    return chunks


def _find_chunk_breakpoint(text: str, start: int, max_end: int) -> int:
    preferred_breaks = ["\n\n", "\n", ". ", " "]

    for delimiter in preferred_breaks:
        split_at = text.rfind(delimiter, start, max_end)
        if split_at > start:
            return split_at + len(delimiter)

    return max_end
