from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

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


class TaskStore:
    """Stores the reception queue locally without saving sign video."""

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
        updated = ReceptionTask(
            **{
                **asdict(task),
                "status": status,
                "updated_at": now,
                "completed_at": completed_at,
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

    def summary(self) -> dict[str, float | int | None]:
        tasks = list(self._tasks.values())
        completed = [task for task in tasks if task.status == TaskStatus.COMPLETED]
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
        }

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
            "version": 1,
            "tasks": [asdict(task) for task in self.list_tasks()],
        }
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
