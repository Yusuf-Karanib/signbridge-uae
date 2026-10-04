from __future__ import annotations

import sys
import time

import cv2


def measure(
    name: str,
    backend: int,
    width: int,
    height: int,
    *,
    mjpg: bool,
    seconds: float = 2.5,
) -> None:
    camera = cv2.VideoCapture(0, backend)
    if not camera.isOpened():
        print(f"{name}: could not open")
        return
    if mjpg:
        camera.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    camera.set(cv2.CAP_PROP_FPS, 30)
    camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    started = time.perf_counter()
    frames = 0
    failures = 0
    consecutive_failures = 0
    while time.perf_counter() - started < seconds:
        ok, _ = camera.read()
        if ok:
            frames += 1
            consecutive_failures = 0
        else:
            failures += 1
            consecutive_failures += 1
            if consecutive_failures >= 10:
                break
    elapsed = time.perf_counter() - started
    width = int(camera.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(camera.get(cv2.CAP_PROP_FRAME_HEIGHT))
    reported_fps = camera.get(cv2.CAP_PROP_FPS)
    fourcc_value = int(camera.get(cv2.CAP_PROP_FOURCC))
    fourcc = "".join(chr((fourcc_value >> (8 * index)) & 0xFF) for index in range(4))
    camera.release()
    print(
        f"{name}: {frames / elapsed:.1f} measured FPS, "
        f"camera reports {reported_fps:.1f} FPS at {width}x{height}, "
        f"format {fourcc!r}, {failures} failed reads"
    )


def main() -> int:
    if not sys.platform.startswith("win"):
        measure("Automatic", cv2.CAP_ANY, 640, 480, mjpg=False)
        return 0
    configurations = (
        ("DirectShow 640x480 default", 640, 480, False),
        ("DirectShow 640x480 MJPG", 640, 480, True),
        ("DirectShow 640x360 MJPG", 640, 360, True),
        ("DirectShow 960x540 MJPG", 960, 540, True),
        ("DirectShow 1280x720 MJPG", 1280, 720, True),
    )
    for name, width, height, mjpg in configurations:
        measure(name, cv2.CAP_DSHOW, width, height, mjpg=mjpg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
