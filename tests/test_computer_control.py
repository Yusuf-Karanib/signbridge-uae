from __future__ import annotations

import unittest

from signbridge.computer_control import ComputerController


class FakeUser32:
    def __init__(self) -> None:
        self.keys: list[tuple[int, int]] = []
        self.pointer: tuple[int, int] | None = None
        self.mouse_flags: list[int] = []

    def keybd_event(self, key: int, _scan: int, flags: int, _extra: int) -> None:
        self.keys.append((key, flags))

    def GetSystemMetrics(self, index: int) -> int:
        return 1920 if index == 0 else 1080

    def SetCursorPos(self, x: int, y: int) -> int:
        self.pointer = (x, y)
        return 1

    def GetCursorPos(self, pointer: object) -> int:
        pointer._obj.x = 960
        pointer._obj.y = 540
        return 1

    def mouse_event(
        self, flags: int, _dx: int, _dy: int, _data: int, _extra: int
    ) -> None:
        self.mouse_flags.append(flags)


class ComputerControllerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user32 = FakeUser32()
        self.controller = ComputerController(self.user32)

    def test_media_and_slide_keys_are_pressed_and_released(self) -> None:
        self.assertTrue(self.controller.volume_up())
        self.assertTrue(self.controller.volume_down())
        self.assertTrue(self.controller.next_slide())
        self.assertTrue(self.controller.previous_slide())
        expected_keys = (0xAF, 0xAE, 0x27, 0x25)
        for index, key in enumerate(expected_keys):
            self.assertEqual(self.user32.keys[index * 2], (key, 0))
            self.assertEqual(self.user32.keys[index * 2 + 1], (key, 0x0002))

    def test_pointer_coordinates_are_clamped_to_screen(self) -> None:
        self.assertTrue(self.controller.move_pointer(1.2, -0.2))
        self.assertEqual(self.user32.pointer, (1919, 0))

    def test_pointer_position_is_returned_as_screen_fraction(self) -> None:
        position = self.controller.pointer_position()

        self.assertIsNotNone(position)
        self.assertAlmostEqual(position[0], 960 / 1919)
        self.assertAlmostEqual(position[1], 540 / 1079)

    def test_click_sends_down_then_up(self) -> None:
        self.assertTrue(self.controller.click())
        self.assertEqual(self.user32.mouse_flags, [0x0002, 0x0004])

    def test_unsupported_controller_does_nothing(self) -> None:
        controller = ComputerController(user32=None)
        controller._user32 = None
        self.assertFalse(controller.volume_up())
        self.assertFalse(controller.move_pointer(0.5, 0.5))
        self.assertIsNone(controller.pointer_position())
        self.assertFalse(controller.click())


if __name__ == "__main__":
    unittest.main()
