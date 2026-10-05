from __future__ import annotations

from datetime import datetime
from pathlib import Path
import ctypes
import sys
import traceback


PROJECT_ROOT = Path(__file__).resolve().parent
STARTUP_LOG = PROJECT_ROOT / "outputs" / "startup.log"


def _report_uncaught_error(
    error_type: type[BaseException], error: BaseException, trace: object
) -> None:
    details = "".join(traceback.format_exception(error_type, error, trace))
    try:
        STARTUP_LOG.parent.mkdir(parents=True, exist_ok=True)
        with STARTUP_LOG.open("a", encoding="utf-8") as log:
            log.write(f"\n[{datetime.now().astimezone().isoformat()}]\n{details}")
    except OSError:
        pass

    message = (
        "SignBridge could not start.\n\n"
        f"The technical details were saved here:\n{STARTUP_LOG}"
    )
    if sys.platform.startswith("win"):
        try:
            ctypes.windll.user32.MessageBoxW(None, message, "SignBridge UAE", 0x10)
            return
        except (AttributeError, OSError):
            pass
    print(message, file=sys.stderr)
    print(details, file=sys.stderr)


def main() -> int:
    try:
        from PySide6.QtCore import QTimer
        from PySide6.QtWidgets import QApplication

        from signbridge.config import ensure_project_directories
        from signbridge.ui import MainWindow

        ensure_project_directories()
        app = QApplication(sys.argv)
        app.setApplicationName("SignBridge UAE")
        app.setOrganizationName("SignBridge UAE")
        window = MainWindow()
        screen = app.primaryScreen()
        if screen is not None:
            available = screen.availableGeometry()
            window.move(available.center() - window.rect().center())
        window.show()
        QTimer.singleShot(0, window.raise_)
        QTimer.singleShot(0, window.activateWindow)
        return app.exec()
    except Exception:
        _report_uncaught_error(*sys.exc_info())
        return 1


if __name__ == "__main__":
    sys.excepthook = _report_uncaught_error
    raise SystemExit(main())

