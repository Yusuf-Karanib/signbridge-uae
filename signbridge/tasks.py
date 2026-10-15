from __future__ import annotations

import json
import re
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from statistics import median

from signbridge.config import AGENT_TASKS_PATH


TASK_ID_PATTERN = re.compile(r"^SB-(\d+)$")


class TaskStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    COMPLETED = "completed"


class DeliveryStatus(str, Enum):
    NOT_CONFIGURED = "not_configured"
    SENDING = "sending"
    SENT = "sent"
    FAILED = "failed"


class TaskOutcome(str, Enum):
    UNREVIEWED = "unreviewed"
    SUCCESS = "success"
    WRONG_ACTION = "wrong_action"
    CANCELLED = "cancelled"


class VisitorOutcome(str, Enum):
    NOT_RECORDED = "not_recorded"
    RESOLVED = "resolved"
    NEEDS_HELP = "needs_help"


@dataclass(frozen=True)
class ReceptionTask:
    id: str
    action_id: str
    title: str
    message: str
    language: str
    status: TaskStatus
    created_at: str
    updated_at: str
    completed_at: str | None = None
    staff_reply: str = ""
    delivery_status: DeliveryStatus = DeliveryStatus.NOT_CONFIGURED
    delivery_message: str = ""
    input_method: str = "unknown"
    correction_used: bool = False
    confidence: float | None = None
    outcome: TaskOutcome = TaskOutcome.UNREVIEWED
    visitor_outcome: VisitorOutcome = VisitorOutcome.NOT_RECORDED
    visitor_confirmed_at: str | None = None


class TaskStore:
    """Stores the service queue locally without saving sign video."""

    def __init__(self, path: Path | None = AGENT_TASKS_PATH) -> None:
        self.path = Path(path) if path is not None else None
        self._tasks: dict[str, ReceptionTask] = {}
        self.load_error: str | None = None
        self._load()

    @classmethod
    def in_memory(cls) -> "TaskStore":
        return cls(path=None)

    def create(
        self,
        *,
        action_id: str,
        title: str,
        message: str,
        language: str,
        input_method: str = "unknown",
        correction_used: bool = False,
        confidence: float | None = None,
    ) -> ReceptionTask:
        self._raise_if_unreadable()
        now = datetime.now(timezone.utc).isoformat()
        task = ReceptionTask(
            id=self._next_id(),
            action_id=str(action_id),
            title=str(title).strip(),
            message=str(message).strip(),
            language=str(language),
            status=TaskStatus.PENDING,
            created_at=now,
            updated_at=now,
            input_method=str(input_method).strip() or "unknown",
            correction_used=bool(correction_used),
            confidence=(float(confidence) if confidence is not None else None),
        )
        self._tasks[task.id] = task
        self._save()
        return task

    def get(self, task_id: str) -> ReceptionTask | None:
        return self._tasks.get(str(task_id))

    def list_tasks(self, include_completed: bool = True) -> list[ReceptionTask]:
        tasks = list(self._tasks.values())
        if not include_completed:
            tasks = [task for task in tasks if task.status != TaskStatus.COMPLETED]
        return sorted(tasks, key=lambda task: task.created_at, reverse=True)

    def update_status(self, task_id: str, status: TaskStatus) -> ReceptionTask:
        task = self._required(task_id)
        now = datetime.now(timezone.utc).isoformat()
        completed_at = now if status == TaskStatus.COMPLETED else None
        awaiting_new_guest_check = (
            status == TaskStatus.COMPLETED
            and task.visitor_outcome == VisitorOutcome.NEEDS_HELP
        )
        updated = ReceptionTask(
            **{
                **asdict(task),
                "status": status,
                "updated_at": now,
                "completed_at": completed_at,
                "visitor_outcome": (
                    VisitorOutcome.NOT_RECORDED
                    if awaiting_new_guest_check
                    else task.visitor_outcome
                ),
                "visitor_confirmed_at": (
                    None
                    if awaiting_new_guest_check
                    else task.visitor_confirmed_at
                ),
            }
        )
        self._tasks[task.id] = updated
        self._save()
        return updated

    def add_reply(self, task_id: str, reply: str) -> ReceptionTask:
        clean_reply = str(reply).strip()
        if not clean_reply:
            raise ValueError("Enter a staff reply first")
        task = self._required(task_id)
        updated = ReceptionTask(
            **{
                **asdict(task),
                "staff_reply": clean_reply[:500],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._tasks[task.id] = updated
        self._save()
        return updated

    def mark_delivery(
        self,
        task_id: str,
        status: DeliveryStatus,
        message: str = "",
    ) -> ReceptionTask:
        task = self._required(task_id)
        updated = ReceptionTask(
            **{
                **asdict(task),
                "delivery_status": status,
                "delivery_message": str(message).strip()[:500],
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
        )
        self._tasks[task.id] = updated
        self._save()
        return updated

    def mark_outcome(
        self, task_id: str, outcome: TaskOutcome
    ) -> ReceptionTask:
        if outcome == TaskOutcome.UNREVIEWED:
            raise ValueError("Choose a completed outcome")
        task = self._required(task_id)
        now = datetime.now(timezone.utc).isoformat()
        updated = ReceptionTask(
            **{
                **asdict(task),
                "status": TaskStatus.COMPLETED,
                "outcome": outcome,
                "updated_at": now,
                "completed_at": task.completed_at or now,
            }
        )
        self._tasks[task.id] = updated
        self._save()
        return updated

    def mark_visitor_outcome(
        self, task_id: str, visitor_outcome: VisitorOutcome
    ) -> ReceptionTask:
        if visitor_outcome == VisitorOutcome.NOT_RECORDED:
            raise ValueError("Choose whether the visitor's request was resolved")
        task = self._required(task_id)
        if task.status != TaskStatus.COMPLETED:
            raise ValueError(
                "Hotel staff must mark the service as delivered before the guest confirms the outcome"
            )
        if task.outcome in (TaskOutcome.WRONG_ACTION, TaskOutcome.CANCELLED):
            raise ValueError(
                "A wrong or cancelled task cannot be confirmed as a delivered service"
            )
        now = datetime.now(timezone.utc).isoformat()
        resolved = visitor_outcome == VisitorOutcome.RESOLVED
        updated = ReceptionTask(
            **{
                **asdict(task),
                "status": TaskStatus.COMPLETED if resolved else TaskStatus.ACCEPTED,
                "outcome": TaskOutcome.SUCCESS if resolved else TaskOutcome.UNREVIEWED,
                "updated_at": now,
                "completed_at": (task.completed_at or now) if resolved else None,
                "visitor_outcome": visitor_outcome,
                "visitor_confirmed_at": now,
            }
        )
        self._tasks[task.id] = updated
        self._save()
        return updated

    def clear_all(self) -> int:
        self._raise_if_unreadable()
        count = len(self._tasks)
        self._tasks.clear()
        self._save()
        return count

    def summary(self) -> dict[str, float | int | None]:
        tasks = list(self._tasks.values())
        completed = [task for task in tasks if task.status == TaskStatus.COMPLETED]
        reviewed = [task for task in tasks if task.outcome != TaskOutcome.UNREVIEWED]
        successful = [task for task in tasks if task.outcome == TaskOutcome.SUCCESS]
        wrong = [task for task in tasks if task.outcome == TaskOutcome.WRONG_ACTION]
        cancelled = [task for task in tasks if task.outcome == TaskOutcome.CANCELLED]
        visitor_reviewed = [
            task
            for task in tasks
            if task.visitor_outcome != VisitorOutcome.NOT_RECORDED
        ]
        visitor_resolved = [
            task for task in tasks if task.visitor_outcome == VisitorOutcome.RESOLVED
        ]
        visitor_needs_help = [
            task for task in tasks if task.visitor_outcome == VisitorOutcome.NEEDS_HELP
        ]
        judged_actions = successful + wrong
        completion_seconds: list[float] = []
        for task in completed:
            if not task.completed_at:
                continue
            try:
                started = datetime.fromisoformat(task.created_at)
                finished = datetime.fromisoformat(task.completed_at)
                completion_seconds.append(max(0.0, (finished - started).total_seconds()))
            except ValueError:
                continue
        return {
            "total": len(tasks),
            "pending": sum(task.status == TaskStatus.PENDING for task in tasks),
            "accepted": sum(task.status == TaskStatus.ACCEPTED for task in tasks),
            "completed": len(completed),
            "reviewed": len(reviewed),
            "successful": len(successful),
            "wrong_action": len(wrong),
            "cancelled": len(cancelled),
            "visitor_confirmed": len(visitor_reviewed),
            "visitor_resolved": len(visitor_resolved),
            "visitor_needs_help": len(visitor_needs_help),
            "corrections": sum(task.correction_used for task in tasks),
            "sent": sum(
                task.delivery_status == DeliveryStatus.SENT for task in tasks
            ),
            "failed_delivery": sum(
                task.delivery_status == DeliveryStatus.FAILED for task in tasks
            ),
            "average_completion_seconds": (
                sum(completion_seconds) / len(completion_seconds)
                if completion_seconds
                else None
            ),
            "median_completion_seconds": (
                median(completion_seconds) if completion_seconds else None
            ),
            "task_completion_rate": (
                len(successful) / len(tasks) if tasks else None
            ),
            "false_action_rate": (
                len(wrong) / len(judged_actions) if judged_actions else None
            ),
            "correction_rate": (
                sum(task.correction_used for task in tasks) / len(tasks)
                if tasks
                else None
            ),
            "visitor_resolution_rate": (
                len(visitor_resolved) / len(visitor_reviewed)
                if visitor_reviewed
                else None
            ),
        }

    def write_evidence_report(self, path: Path) -> Path:
        self._raise_if_unreadable()
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        tasks = list(self._tasks.values())
        payload = {
            "version": 2,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "privacy_note": (
                "This aggregate report excludes staff replies, webhook URLs, "
                "camera data and participant identifiers."
            ),
            "summary": self.summary(),
            "tasks_by_action": dict(Counter(task.action_id for task in tasks)),
            "tasks_by_language": dict(Counter(task.language for task in tasks)),
            "tasks_by_input_method": dict(
                Counter(task.input_method for task in tasks)
            ),
        }
        temporary = destination.with_suffix(destination.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(destination)
        return destination

    def _required(self, task_id: str) -> ReceptionTask:
        self._raise_if_unreadable()
        task = self.get(task_id)
        if task is None:
            raise ValueError(f"Task {task_id} was not found")
        return task

    def _next_id(self) -> str:
        numbers = []
        for task_id in self._tasks:
            match = TASK_ID_PATTERN.fullmatch(task_id)
            if match:
                numbers.append(int(match.group(1)))
        return f"SB-{(max(numbers, default=0) + 1):03d}"

    def _raise_if_unreadable(self) -> None:
        if self.load_error:
            raise RuntimeError(self.load_error)

    def _load(self) -> None:
        if self.path is None or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            tasks = payload.get("tasks", [])
            self._tasks = {
                str(item["id"]): ReceptionTask(
                    id=str(item["id"]),
                    action_id=str(item["action_id"]),
                    title=str(item["title"]),
                    message=str(item["message"]),
                    language=str(item["language"]),
                    status=TaskStatus(item["status"]),
                    created_at=str(item["created_at"]),
                    updated_at=str(item["updated_at"]),
                    completed_at=(
                        str(item["completed_at"])
                        if item.get("completed_at")
                        else None
                    ),
                    staff_reply=str(item.get("staff_reply", "")),
                    delivery_status=DeliveryStatus(
                        item.get("delivery_status", DeliveryStatus.NOT_CONFIGURED)
                    ),
                    delivery_message=str(item.get("delivery_message", "")),
                    input_method=str(item.get("input_method", "unknown")),
                    correction_used=bool(item.get("correction_used", False)),
                    confidence=(
                        float(item["confidence"])
                        if item.get("confidence") is not None
                        else None
                    ),
                    outcome=TaskOutcome(
                        item.get("outcome", TaskOutcome.UNREVIEWED)
                    ),
                    visitor_outcome=VisitorOutcome(
                        item.get("visitor_outcome", VisitorOutcome.NOT_RECORDED)
                    ),
                    visitor_confirmed_at=(
                        str(item["visitor_confirmed_at"])
                        if item.get("visitor_confirmed_at")
                        else None
                    ),
                )
                for item in tasks
            }
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self._tasks = {}
            self.load_error = (
                f"The local task file could not be read: {exc}. "
                "It was left untouched so it can be recovered."
            )

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 2,
            "tasks": [asdict(task) for task in self.list_tasks()],
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
