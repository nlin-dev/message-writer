from __future__ import annotations

import re


def chunk_text(text: str, max_chunk_size: int = 500) -> list[str]:
    if not text.strip():
        return []

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if current and len(current) + 1 + len(sentence) > max_chunk_size:
            chunks.append(current)
            current = sentence
        elif current:
            current += " " + sentence
        else:
            current = sentence

    if current:
        chunks.append(current)

    return chunks
