from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from signbridge.config import VALIDATION_PATH


class ValidationStore:
    def __init__(self, path: Path = VALIDATION_PATH):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict:
        if not self.path.exists():
            return {"version": 1, "languages": {}}
        try:
            return json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {"version": 1, "languages": {}}

    def mark_reviewed(self, language: str, label: str, validator: str) -> None:
        validator = validator.strip()
        if not validator:
            raise ValueError("Enter the fluent signer's or interpreter's name")
        payload = self.load()
        language_entries = payload.setdefault("languages", {}).setdefault(language, {})
        language_entries[label] = {
            "reviewed": True,
            "validator": validator,
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)

    def is_reviewed(self, language: str, label: str) -> bool:
        entry = self.load().get("languages", {}).get(language, {}).get(label, {})
        return bool(entry.get("reviewed"))

    def reviewed_count(self, language: str, labels: tuple[str, ...]) -> int:
        return sum(self.is_reviewed(language, label) for label in labels)

