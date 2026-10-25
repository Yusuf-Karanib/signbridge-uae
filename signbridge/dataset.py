from __future__ import annotations

import json
import re
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from signbridge.config import SAMPLES_DIR, TRASH_DIR, SEQUENCE_LENGTH
from signbridge.landmarks import FEATURE_DIM, FEATURE_VERSION


SAFE_COMPONENT = re.compile(r"[^a-zA-Z0-9_-]+")


@dataclass(frozen=True)
class SampleRecord:
    path: Path
    language: str
    label: str
    person_id: str
    sequence: np.ndarray
    metadata: dict


class DatasetStore:
    def __init__(self, samples_dir: Path = SAMPLES_DIR, trash_dir: Path = TRASH_DIR):
        self.samples_dir = Path(samples_dir)
        self.trash_dir = Path(trash_dir)
        self.last_delete_skipped = 0
        self.samples_dir.mkdir(parents=True, exist_ok=True)
        self.trash_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def safe_component(value: str) -> str:
        cleaned = SAFE_COMPONENT.sub("-", value.strip()).strip("-")
        if not cleaned:
            raise ValueError("A person identifier is required")
        return cleaned[:60]

    def save_sample(
        self,
        language: str,
        label: str,
        person_id: str,
        sequence: np.ndarray,
        quality: dict | None = None,
        consent_confirmed: bool = False,
        capture_source: str = "unknown",
    ) -> Path:
        person_id = self.safe_component(person_id)
        language = self.safe_component(language)
        label = self.safe_component(label)
        sequence = np.asarray(sequence, dtype=np.float32)
        if sequence.shape != (SEQUENCE_LENGTH, FEATURE_DIM) or not np.isfinite(sequence).all():
            raise ValueError("The landmark sample is incomplete or invalid. Record it again.")
        timestamp = datetime.now(timezone.utc)
        destination = self.samples_dir / language / label
        destination.mkdir(parents=True, exist_ok=True)
        filename = f"{timestamp.strftime('%Y%m%dT%H%M%S%fZ')}_{uuid.uuid4().hex[:8]}.npz"
        path = destination / filename
        metadata = {
            "version": 1,
            "feature_version": FEATURE_VERSION,
            "feature_dim": FEATURE_DIM,
            "language": language,
            "label": label,
            "person_id": person_id,
            "captured_at": timestamp.isoformat(),
            "quality": quality or {},
            "consent_confirmed": bool(consent_confirmed),
            "capture_source": str(capture_source).strip() or "unknown",
        }
        temporary = path.with_suffix(".tmp")
        with temporary.open("wb") as output:
            np.savez_compressed(output, sequence=sequence, metadata=json.dumps(metadata))
        temporary.replace(path)
        return path

    def load_records(self, language: str | None = None) -> list[SampleRecord]:
        root = self.samples_dir / language if language else self.samples_dir
        if not root.exists():
            return []
        records: list[SampleRecord] = []
        for path in sorted(root.rglob("*.npz")):
            try:
                with np.load(path, allow_pickle=False) as payload:
                    sequence = np.asarray(payload["sequence"], dtype=np.float32)
                    metadata_raw = payload["metadata"].item()
                metadata = json.loads(str(metadata_raw))
                if not isinstance(metadata, dict) or not all(
                    isinstance(metadata.get(key), str)
                    for key in ("language", "label", "person_id")
                ) or not isinstance(metadata.get("quality", {}), dict):
                    continue
                if metadata.get("feature_version") != FEATURE_VERSION:
                    continue
                if sequence.shape != (SEQUENCE_LENGTH, FEATURE_DIM) or not np.isfinite(sequence).all():
                    continue
                records.append(
                    SampleRecord(
                        path=path,
                        language=metadata["language"],
                        label=metadata["label"],
                        person_id=metadata["person_id"],
                        sequence=sequence,
                        metadata=metadata,
                    )
                )
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        return records

    def counts(self, language: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for record in self.load_records(language):
            counts[record.label] = counts.get(record.label, 0) + 1
        return counts

    def people(self, language: str) -> set[str]:
        return {record.person_id for record in self.load_records(language)}

    def video_hashes(self, language: str) -> set[str]:
        return {
            str(record.metadata.get("quality", {}).get("video_sha256"))
            for record in self.load_records(language)
            if record.metadata.get("quality", {}).get("video_sha256")
        }

    def move_last_to_trash(self, language: str, label: str) -> Path | None:
        candidates = [
            record.path
            for record in self.load_records(language)
            if record.label == label
        ]
        if not candidates:
            return None
        source = max(candidates, key=lambda item: item.stat().st_mtime_ns)
        destination_dir = self.trash_dir / language / label
        destination_dir.mkdir(parents=True, exist_ok=True)
        destination = destination_dir / source.name
        shutil.move(str(source), str(destination))
        return destination

    def delete_person(self, person_id: str, language: str | None = None) -> int:
        """Permanently delete one person's landmark samples, including trash."""
        self.last_delete_skipped = 0
        safe_person = self.safe_component(person_id).casefold()
        safe_language = self.safe_component(language) if language else None
        removed = 0
        for base in (self.samples_dir, self.trash_dir):
            root = base / safe_language if safe_language else base
            if not root.exists():
                continue
            for path in list(root.rglob("*.npz")):
                try:
                    with np.load(path, allow_pickle=False) as payload:
                        metadata = json.loads(str(payload["metadata"].item()))
                    if str(metadata.get("person_id", "")).casefold() != safe_person:
                        continue
                    path.unlink()
                    removed += 1
                except (OSError, KeyError, ValueError, json.JSONDecodeError):
                    self.last_delete_skipped += 1
                    continue
            for directory in sorted(
                (item for item in root.rglob("*") if item.is_dir()),
                key=lambda item: len(item.parts),
                reverse=True,
            ):
                try:
                    directory.rmdir()
                except OSError:
                    pass
        return removed

