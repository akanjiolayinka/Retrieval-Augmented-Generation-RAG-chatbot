import re


def clean_text(raw_text: str) -> str:
    """Normalize parser output while preserving paragraph boundaries."""
    normalized = raw_text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\t\f\v]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    # Trim per-line noise and collapse repeated spaces.
    cleaned_lines = [re.sub(r" {2,}", " ", line).strip() for line in normalized.split("\n")]
    normalized = "\n".join(cleaned_lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()
