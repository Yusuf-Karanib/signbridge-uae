from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signbridge.tasks import (
    DeliveryStatus,
    TaskOutcome,
    TaskStatus,
    TaskStore,
    VisitorOutcome,
)


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
                input_method="camera",
                correction_used=False,
                confidence=0.91,
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
            store.mark_outcome(first.id, TaskOutcome.SUCCESS)
            store.mark_visitor_outcome(first.id, VisitorOutcome.RESOLVED)

            reloaded = TaskStore(path)
            task = reloaded.get(first.id)
            self.assertIsNotNone(task)
            self.assertEqual(task.status, TaskStatus.COMPLETED)
            self.assertEqual(task.staff_reply, "I will help you now.")
            self.assertEqual(task.delivery_status, DeliveryStatus.SENT)
            self.assertEqual(task.outcome, TaskOutcome.SUCCESS)
            self.assertEqual(task.visitor_outcome, VisitorOutcome.RESOLVED)
            self.assertIsNotNone(task.visitor_confirmed_at)
            self.assertEqual(task.input_method, "camera")
            self.assertEqual(task.confidence, 0.91)
            summary = reloaded.summary()
            self.assertEqual(summary["pending"], 1)
            self.assertEqual(summary["completed"], 1)
            self.assertEqual(summary["sent"], 1)
            self.assertEqual(summary["successful"], 1)
            self.assertEqual(summary["visitor_confirmed"], 1)
            self.assertEqual(summary["visitor_resolved"], 1)
            self.assertEqual(summary["visitor_resolution_rate"], 1.0)
            self.assertEqual(summary["false_action_rate"], 0.0)

            reloaded.mark_outcome(second.id, TaskOutcome.WRONG_ACTION)
            report_path = reloaded.write_evidence_report(
                Path(temp) / "evidence.json"
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
            self.assertEqual(report["summary"]["wrong_action"], 1)
            self.assertEqual(report["summary"]["false_action_rate"], 0.5)
            self.assertNotIn("I will help you now", report_path.read_text(encoding="utf-8"))

            cancelled = reloaded.create(
                action_id="interpreter",
                title="Interpreter task",
                message="Request an interpreter",
                language="asl",
            )
            reloaded.mark_outcome(cancelled.id, TaskOutcome.CANCELLED)
            self.assertEqual(reloaded.summary()["false_action_rate"], 0.5)
            with self.assertRaises(ValueError):
                reloaded.mark_visitor_outcome(
                    cancelled.id, VisitorOutcome.NEEDS_HELP
                )

            delivered = reloaded.create(
                action_id="hotel_service",
                title="Hotel service task",
                message="Help with a hotel service",
                language="asl",
            )
            reloaded.update_status(delivered.id, TaskStatus.COMPLETED)
            reopened = reloaded.mark_visitor_outcome(
                delivered.id, VisitorOutcome.NEEDS_HELP
            )
            self.assertEqual(reopened.status, TaskStatus.ACCEPTED)
            self.assertEqual(reopened.outcome, TaskOutcome.UNREVIEWED)
            self.assertEqual(reopened.visitor_outcome, VisitorOutcome.NEEDS_HELP)

            delivered_again = reloaded.update_status(
                delivered.id, TaskStatus.COMPLETED
            )
            self.assertEqual(
                delivered_again.visitor_outcome,
                VisitorOutcome.NOT_RECORDED,
            )
            self.assertIsNone(delivered_again.visitor_confirmed_at)

            self.assertEqual(reloaded.clear_all(), 4)
            self.assertEqual(reloaded.summary()["total"], 0)

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

    def test_existing_tasks_load_before_guest_confirmation_fields_exist(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "tasks.json"
            path.write_text(
                json.dumps(
                    {
                        "version": 1,
                        "tasks": [
                            {
                                "id": "SB-001",
                                "action_id": "interpreter",
                                "title": "Interpreter task",
                                "message": "Local task",
                                "language": "asl",
                                "status": "pending",
                                "created_at": "2026-10-14T10:00:00+00:00",
                                "updated_at": "2026-10-14T10:00:00+00:00",
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            task = TaskStore(path).get("SB-001")

            self.assertIsNotNone(task)
            self.assertEqual(task.visitor_outcome, VisitorOutcome.NOT_RECORDED)
            self.assertIsNone(task.visitor_confirmed_at)


if __name__ == "__main__":
    unittest.main()
