import re

_WS_RE = re.compile(r"\s+")


def chunk_text(text: str, size: int, overlap: int) -> list[str]:
    if overlap >= size:
        raise ValueError("overlap must be smaller than size")
    text = _WS_RE.sub(" ", text).strip()
    if not text:
        return []

    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        if end < len(text):
            space = text.rfind(" ", start, end)
            if space > start:
                end = space
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        next_start = end - overlap
        space = text.find(" ", next_start, end)
        next_start = space + 1 if space != -1 else next_start
        start = next_start if next_start > start else end
    return chunks
