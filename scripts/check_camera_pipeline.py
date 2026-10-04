from __future__ import annotations

from pathlib import Path
import sys

from PySide6.QtCore import QCoreApplication, QTimer

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from signbridge.camera import CameraWorker


def main() -> int:
    app = QCoreApplication([])
    worker = CameraWorker()
    capture_requested = False
    completed = False

    def request_capture(message: str, ok: bool) -> None:
        nonlocal capture_requested
        print(message, flush=True)
        if ok and not capture_requested:
            capture_requested = True
            QTimer.singleShot(
                500,
                lambda: worker.request_capture(
                    {"purpose": "diagnostic", "language": "none"}
                ),
            )
        elif not ok:
            app.quit()

    def report_performance(message: str) -> None:
        print(message, flush=True)

    def finish(sequence: object, context: object, quality: object) -> None:
        nonlocal completed
        completed = True
        print(f"Sequence shape: {getattr(sequence, 'shape', None)}", flush=True)
        print(f"Capture quality: {quality}", flush=True)
        app.quit()

    def timeout() -> None:
        if not completed:
            print("Camera diagnostic timed out", flush=True)
            app.quit()

    worker.camera_status.connect(request_capture)
    worker.performance_status.connect(report_performance)
    worker.sequence_ready.connect(finish)
    QTimer.singleShot(15_000, timeout)
    worker.start()
    exit_code = app.exec()
    worker.stop()
    return 0 if completed else max(1, exit_code)


if __name__ == "__main__":
    raise SystemExit(main())
