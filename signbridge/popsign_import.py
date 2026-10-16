from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from signbridge.dataset import DatasetStore
from signbridge.video_import import ALLOWED_VIDEO_EXTENSIONS


POPSIGN_DATASET_NAME = "PopSign ASL v2.1"
POPSIGN_CAPTURE_SOURCE = "licensed_dataset:popsign_v2_1_cc_by_4_0"
POPSIGN_LICENSE = "CC BY 4.0"
POPSIGN_MAX_CLIPS_PER_IMPORT = 30

# These are the current SignBridge ASL labels that the published PopSign
# vocabulary actually contains. "Again" must not be silently substituted.
POPSIGN_SUPPORTED_LABELS = frozenset({"hello", "help", "water"})


@dataclass(frozen=True)
class PopSignClip:
    path: Path
    label: str
    person_id: str
    clip_id: str


def _label_for_path(root: Path, path: Path) -> str | None:
    relative = path.relative_to(root)
    parts = (root.name.casefold(),) + tuple(
        part.casefold() for part in relative.parts[:-1]
    )
    matches = [part for part in parts if part in POPSIGN_SUPPORTED_LABELS]
    return matches[-1] if matches else None


def _participant_from_filename(path: Path) -> str | None:
    # PopSign documents filenames as
    # <participant_id>--<recording_start_time>-.mp4.
    if "--" not in path.stem:
        return None
    participant = path.stem.split("--", 1)[0].strip()
    if not participant:
        return None
    try:
        return f"popsign-{DatasetStore.safe_component(participant)}"
    except ValueError:
        return None


def _round_robin_people(clips: Iterable[PopSignClip]) -> list[PopSignClip]:
    """Prefer signer variety instead of taking many adjacent clips from one person."""
    grouped: dict[str, deque[PopSignClip]] = defaultdict(deque)
    for clip in sorted(clips, key=lambda item: (item.person_id, item.path.name)):
        grouped[clip.person_id].append(clip)

    ordered: list[PopSignClip] = []
    people = sorted(grouped)
    while people:
        remaining: list[str] = []
        for person in people:
            ordered.append(grouped[person].popleft())
            if grouped[person]:
                remaining.append(person)
        people = remaining
    return ordered


def discover_popsign_training_clips(
    root: Path,
    *,
    excluded_clip_ids: Iterable[str] = (),
    excluded_people: Iterable[str] = (),
    limit: int = POPSIGN_MAX_CLIPS_PER_IMPORT,
) -> tuple[PopSignClip, ...]:
    """Find one sign's original PopSign TRAIN clips without mixing test data.

    This function does not download, copy, or decode videos. It validates the
    selected directory and returns a diverse, bounded list for the UI worker.
    """
    root = Path(root)
    if not root.is_dir():
        raise ValueError("Choose an extracted PopSign sign folder.")
    if limit < 1:
        raise ValueError("The import limit must be at least one clip.")

    path_parts = {part.casefold() for part in root.parts}
    if path_parts.intersection({"val", "validation", "test"}):
        raise ValueError(
            "This looks like validation or test data. Keep it out of training."
        )
    if "train" not in path_parts:
        raise ValueError(
            "Choose a folder inside the official PopSign 'train' split."
        )
    if "game" not in path_parts or path_parts.intersection(
        {"non-game", "non_game", "nongame", "variant", "variants"}
    ):
        raise ValueError(
            "Choose the official PopSign 'game/train' example folder, not a variant folder."
        )

    excluded_ids = {str(item).casefold() for item in excluded_clip_ids}
    excluded_person_ids = {str(item).casefold() for item in excluded_people}
    found: list[PopSignClip] = []
    labels: set[str] = set()
    seen_clip_ids: set[str] = set()

    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in ALLOWED_VIDEO_EXTENSIONS:
            continue
        label = _label_for_path(root, path)
        if label is None:
            continue
        labels.add(label)
        person_id = _participant_from_filename(path)
        if person_id is None or person_id.casefold() in excluded_person_ids:
            continue
        clip_id = f"popsign_v2_1/{label}/{path.name}"
        if clip_id.casefold() in excluded_ids or clip_id.casefold() in seen_clip_ids:
            continue
        seen_clip_ids.add(clip_id.casefold())
        found.append(
            PopSignClip(
                path=path,
                label=label,
                person_id=person_id,
                clip_id=clip_id,
            )
        )

    if len(labels) > 1:
        raise ValueError(
            "Choose one sign folder at a time, such as train/hello or train/help."
        )
    if not labels:
        raise ValueError(
            "No supported PopSign folder was found. Current matches are hello, help and water."
        )
    if not found:
        raise ValueError(
            "No new usable clips were found. They may already be imported or belong to final-test people."
        )

    return tuple(_round_robin_people(found)[:limit])
