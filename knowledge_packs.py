"""Offline knowledge pack commands."""

import os
import re
from pathlib import Path

from ingest_docs import ingest_file


KNOWLEDGE_DIR = Path("knowledge")
SUPPORTED_SUFFIXES = {".txt", ".md", ".pdf"}

LIST_PATTERN = re.compile(r"^(?:list|show)\s+(?:offline\s+)?knowledge\s+packs$", re.IGNORECASE)
INGEST_PATTERN = re.compile(r"^(?:ingest|learn)\s+(?:all\s+)?(?:offline\s+)?knowledge\s+packs$", re.IGNORECASE)
STATUS_PATTERN = re.compile(r"^(?:knowledge\s+pack\s+status|offline\s+knowledge\s+status)$", re.IGNORECASE)


def _pack_files():
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    return sorted(
        path for path in KNOWLEDGE_DIR.iterdir()
        if path.is_file() and path.suffix.lower() in SUPPORTED_SUFFIXES
    )


def is_knowledge_pack_request(text):
    normalized = " ".join(str(text).strip().split())
    return bool(LIST_PATTERN.match(normalized) or INGEST_PATTERN.match(normalized) or STATUS_PATTERN.match(normalized))


def handle_knowledge_pack_command(text):
    normalized = " ".join(str(text).strip().split())
    files = _pack_files()

    if LIST_PATTERN.match(normalized) or STATUS_PATTERN.match(normalized):
        if not files:
            return {"action": "knowledge_packs", "reply": "No offline knowledge packs found. Add .txt, .md, or .pdf files to the knowledge folder."}
        total_kb = sum(path.stat().st_size for path in files) / 1024
        names = ", ".join(path.name for path in files[:8])
        more = f", plus {len(files) - 8} more" if len(files) > 8 else ""
        return {
            "action": "knowledge_packs",
            "reply": f"Offline knowledge packs: {len(files)} files, {total_kb:.1f} KB. Files: {names}{more}.",
        }

    if INGEST_PATTERN.match(normalized):
        if not files:
            return {"action": "knowledge_ingest_all", "reply": "There are no offline knowledge packs to ingest yet."}
        total_chunks = 0
        failures = []
        for path in files:
            try:
                total_chunks += ingest_file(os.fspath(path))
            except Exception as exc:
                failures.append(f"{path.name}: {exc}")
        if failures:
            return {
                "action": "knowledge_ingest_all",
                "reply": f"Ingested {total_chunks} sections, but {len(failures)} file failed: {'; '.join(failures[:3])}",
            }
        return {"action": "knowledge_ingest_all", "reply": f"Ingested {total_chunks} sections from {len(files)} offline knowledge pack files."}

    return None
