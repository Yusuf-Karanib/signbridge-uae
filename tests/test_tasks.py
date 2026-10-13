from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signbridge.tasks import DeliveryStatus, TaskStatus, TaskStore


class TaskStoreTests(unittest.TestCase):
    def test_task_lifecycle_persists_and_produces_metrics(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "tasks.json"
            store = TaskStore(path)
            first = store.create(
                action_id="appointment",
                title="Appointment task",
                message="Help with an appointment",
                language="asl",
            )
            second = store.create(
                action_id="request_water",
                title="Water task",
                message="Help with water",
                language="emirati",
            )
            self.assertEqual(first.id, "SB-001")
            self.assertEqual(second.id, "SB-002")

            store.update_status(first.id, TaskStatus.ACCEPTED)
            store.add_reply(first.id, "I will help you now.")
            store.mark_delivery(
                first.id, DeliveryStatus.SENT, "Notification delivered"
            )
            store.update_status(first.id, TaskStatus.COMPLETED)

            reloaded = TaskStore(path)
            task = reloaded.get(first.id)
            self.assertIsNotNone(task)
            self.assertEqual(task.status, TaskStatus.COMPLETED)
            self.assertEqual(task.staff_reply, "I will help you now.")
            self.assertEqual(task.delivery_status, DeliveryStatus.SENT)
            summary = reloaded.summary()
            self.assertEqual(summary["pending"], 1)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["sent"], 1)

    def test_unreadable_task_file_is_not_overwritten(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "tasks.json"
            path.write_text("not valid json", encoding="utf-8")
            store = TaskStore(path)

            self.assertIsNotNone(store.load_error)
            with self.assertRaises(RuntimeError):
                store.create(
                    action_id="help",
                    title="Help",
                    message="Help",
                    language="asl",
                )
            self.assertEqual(path.read_text(encoding="utf-8"), "not valid json")


if __name__ == "__main__":
    unittest.main()
