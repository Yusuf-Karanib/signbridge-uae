from __future__ import annotations

import hashlib
from pathlib import Path

import requests


MODELS = (
    (
        "holistic_landmarker.task",
        "https://storage.googleapis.com/mediapipe-models/holistic_landmarker/"
        "holistic_landmarker/float16/1/holistic_landmarker.task",
        13_000_000,
    ),
    (
        "gesture_recognizer.task",
        "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/"
        "gesture_recognizer/float16/1/gesture_recognizer.task",
        7_000_000,
    ),
)


def download_model(destination: Path, url: str, expected_minimum_bytes: int) -> None:
    if destination.exists() and destination.stat().st_size >= expected_minimum_bytes:
        print(f"MediaPipe model already exists: {destination}")
        return

    print(f"Downloading the official MediaPipe model: {destination.name}…")
    response = requests.get(url, timeout=90)
    response.raise_for_status()
    if len(response.content) < expected_minimum_bytes:
        raise RuntimeError(f"The downloaded {destination.name} file is unexpectedly small")
    temporary = destination.with_suffix(".download")
    temporary.write_bytes(response.content)
    temporary.replace(destination)
    digest = hashlib.sha256(response.content).hexdigest()
    print(f"Saved {len(response.content):,} bytes. SHA-256: {digest}")


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    model_directory = project_root / "assets" / "models"
    model_directory.mkdir(parents=True, exist_ok=True)
    for filename, url, minimum_bytes in MODELS:
        download_model(model_directory / filename, url, minimum_bytes)


if __name__ == "__main__":
    main()

