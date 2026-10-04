from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from signbridge.config import ensure_project_directories
from signbridge.ui import MainWindow


def main() -> int:
    ensure_project_directories()
    app = QApplication(sys.argv)
    app.setApplicationName("SignBridge UAE")
    app.setOrganizationName("SignBridge UAE")
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

