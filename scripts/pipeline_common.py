"""Shared configuration and safe file helpers for the FASP pipeline."""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any


DEFAULT_WORK_DIR = "/Users/adominguezdia/Documents/FASP"
DEFAULT_TOKEN_PATH = "~/.hermes/google_token.json"


def work_dir() -> Path:
    return Path(os.environ.get("FASP_WORK_DIR", DEFAULT_WORK_DIR)).expanduser()


def token_path() -> Path:
    return Path(os.environ.get("FASP_GOOGLE_TOKEN", DEFAULT_TOKEN_PATH)).expanduser()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
    temporary.replace(path)


def drive_local_path(remote_path: str, file_id: str) -> Path:
    """Produce a stable local name that cannot collide with another Drive file."""
    path = Path(remote_path)
    safe_id = re.sub(r"[^A-Za-z0-9]", "", file_id)[:16]
    return path.with_name(f"{path.stem}__drive-{safe_id}{path.suffix}")


def content_label(text: str, title: str = "") -> str:
    """Return a readable, stable label from PDF metadata or its first useful heading."""
    candidates = [title] + text.splitlines()
    for candidate in candidates:
        compact = re.sub(r"\s+", " ", candidate).strip()
        if len(compact) < 8 or not re.search(r"[A-Za-zÁÉÍÓÚÑáéíóúñ]", compact):
            continue
        ascii_value = unicodedata.normalize("NFKD", compact).encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^A-Za-z0-9]+", "_", ascii_value).strip("_").upper()
        if normalized:
            return normalized[:72]
    return "CONTENIDO_SIN_TITULO"
