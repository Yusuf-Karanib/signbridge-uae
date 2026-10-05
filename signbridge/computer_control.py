from __future__ import annotations

import ctypes
import sys
from typing import Any


class _Point(ctypes.Structure):
    _fields_ = (("x", ctypes.c_long), ("y", ctypes.c_long))


class ComputerController:
    """Small Windows input wrapper used only after the user enables control mode."""

    KEYEVENTF_KEYUP = 0x0002
    MOUSEEVENTF_LEFTDOWN = 0x0002
    MOUSEEVENTF_LEFTUP = 0x0004

    VK_LEFT = 0x25
    VK_RIGHT = 0x27
    VK_VOLUME_DOWN = 0xAE
    VK_VOLUME_UP = 0xAF

    def __init__(self, user32: Any | None = None) -> None:
        self._user32 = user32
        if self._user32 is None and sys.platform.startswith("win"):
            try:
                self._user32 = ctypes.windll.user32
            except (AttributeError, OSError):
                self._user32 = None

    @property
    def is_supported(self) -> bool:
        return self._user32 is not None

    def _tap_key(self, virtual_key: int) -> bool:
        if self._user32 is None:
            return False
        self._user32.keybd_event(virtual_key, 0, 0, 0)
        self._user32.keybd_event(virtual_key, 0, self.KEYEVENTF_KEYUP, 0)
        return True

    def volume_up(self) -> bool:
        return self._tap_key(self.VK_VOLUME_UP)

    def volume_down(self) -> bool:
        return self._tap_key(self.VK_VOLUME_DOWN)

    def next_slide(self) -> bool:
        return self._tap_key(self.VK_RIGHT)

    def previous_slide(self) -> bool:
        return self._tap_key(self.VK_LEFT)

    def move_pointer(self, normalized_x: float, normalized_y: float) -> bool:
        if self._user32 is None:
            return False
        width = max(1, int(self._user32.GetSystemMetrics(0)))
        height = max(1, int(self._user32.GetSystemMetrics(1)))
        x = int(max(0.0, min(1.0, normalized_x)) * (width - 1))
        y = int(max(0.0, min(1.0, normalized_y)) * (height - 1))
        return bool(self._user32.SetCursorPos(x, y))

    def pointer_position(self) -> tuple[float, float] | None:
        if self._user32 is None:
            return None
        point = _Point()
        if not self._user32.GetCursorPos(ctypes.byref(point)):
            return None
        width = max(1, int(self._user32.GetSystemMetrics(0)))
        height = max(1, int(self._user32.GetSystemMetrics(1)))
        return (
            max(0.0, min(1.0, point.x / max(1, width - 1))),
            max(0.0, min(1.0, point.y / max(1, height - 1))),
        )

    def click(self) -> bool:
        if self._user32 is None:
            return False
        self._user32.mouse_event(self.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        self._user32.mouse_event(self.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        return True
