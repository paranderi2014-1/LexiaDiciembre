"""Utilidades de texto jurídico: normalización, huellas y fragmentación (§9, §10)."""

from __future__ import annotations

import hashlib
import re
import unicodedata

_WHITESPACE = re.compile(r"[ \t\u00a0]+")
_BLANKS = re.compile(r"\n{3,}")


def normalize_text(raw: str) -> str:
    """Unifica espacios y saltos sin alterar el contenido citado."""
    text = unicodedata.normalize("NFC", raw.replace("\r\n", "\n").replace("\r", "\n"))
    text = _WHITESPACE.sub(" ", text)
    return _BLANKS.sub("\n\n", text).strip()


def content_hash(text: str) -> str:
    """Huella usada para deduplicar documentos y versiones (§9).

    Ignora diferencias de formato (saltos de línea, espacios repetidos) para que
    un cambio de maquetado en el portal no cree una versión nueva.
    """
    plano = " ".join(normalize_text(text).split())
    return hashlib.sha256(plano.encode("utf-8")).hexdigest()


def estimate_tokens(text: str) -> int:
    """Estimación conservadora: ~4 caracteres por token en español jurídico."""
    return max(1, len(text) // 4)


def chunk_text(text: str, size: int = 500, overlap: int = 100) -> list[str]:
    """Fragmenta en ventanas de `size` tokens con `overlap` de solapamiento.

    Cada fragmento conserva contexto continuo del documento; el llamador guarda
    el vínculo con documento y artículo (§9).
    """
    if size <= 0:
        raise ValueError("size debe ser positivo")
    if overlap < 0 or overlap >= size:
        raise ValueError("overlap debe ser >= 0 y menor que size")

    clean = normalize_text(text)
    if not clean:
        return []

    words = clean.split(" ")
    # ~0.75 palabras por token es una aproximación razonable para texto legal.
    window = max(1, int(size * 0.75))
    step = max(1, window - int(overlap * 0.75))

    chunks: list[str] = []
    for start in range(0, len(words), step):
        piece = " ".join(words[start : start + window]).strip()
        if piece:
            chunks.append(piece)
        if start + window >= len(words):
            break
    return chunks
