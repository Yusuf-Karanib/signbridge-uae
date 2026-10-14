from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable

from signbridge.assistance import ConversationTurn, RequestOption
from signbridge.tasks import ReceptionTask, TaskStatus, TaskStore


class AgentActionStatus(str, Enum):
    COMPLETED = "completed"
    WAITING_FOR_STAFF = "waiting_for_staff"
    LOCAL_TASK = "local_task"


@dataclass(frozen=True)
class AgentActionResult:
    action_id: str
    title: str
    message: str
    status: AgentActionStatus
    task_id: str | None = None
    external_action_taken: bool = False
    used_conversation_memory: bool = False


ACTION_IDS = frozenset(
    {
        "start",
        "directions",
        "appointment",
        "interpreter",
        "other",
        "request_water",
        "find_water",
        "please_wait",
        "wait_here",
        "repeat",
        "show_again",
    }
)


_ACTION_TEXT = {
    "asl": {
        "start": (
            "Conversation started",
            "The conversation is ready. Staff can type a reply below.",
        ),
        "directions": (
            "Directions task",
            "A local directions task was created. Staff should type the destination and directions below.",
        ),
        "appointment": (
            "Appointment task",
            "A local appointment-help task was created. No booking system was contacted.",
        ),
        "interpreter": (
            "Interpreter task",
            "A local sign-language interpreter task was created. No interpreter service was contacted.",
        ),
        "other": (
            "General assistance task",
            "A local general-assistance task was created. Staff action is required.",
        ),
        "request_water": (
            "Water request task",
            "A local water-assistance task was created. Staff action is required.",
        ),
        "find_water": (
            "Water directions task",
            "A local water-directions task was created. Staff should type the exact venue directions below.",
        ),
        "please_wait": (
            "Wait request shown",
            "The request to wait was shown to staff.",
        ),
        "wait_here": (
            "Waiting state started",
            "The person is waiting here. Staff can type a reply when ready.",
        ),
        "repeat_missing": (
            "Repeat requested",
            "There is no earlier staff reply in this session. Staff should type the reply again.",
        ),
        "previous_reply": (
            "Previous reply found",
            "Last staff reply: {reply}",
        ),
    },
    "emirati": {
        "start": (
            "بدء المحادثة",
            "المحادثة جاهزة. يمكن للموظف كتابة رد أدناه.",
        ),
        "directions": (
            "مهمة الاتجاهات",
            "تم إنشاء مهمة اتجاهات محلية. على الموظف كتابة الوجهة والاتجاهات أدناه.",
        ),
        "appointment": (
            "مهمة الموعد",
            "تم إنشاء مهمة محلية للمساعدة في الموعد. لم يتم الاتصال بأي نظام حجز.",
        ),
        "interpreter": (
            "مهمة مترجم لغة الإشارة",
            "تم إنشاء مهمة محلية لطلب مترجم لغة إشارة. لم يتم الاتصال بخدمة مترجم.",
        ),
        "other": (
            "مهمة مساعدة عامة",
            "تم إنشاء مهمة مساعدة عامة محلية. يلزم تدخل الموظف.",
        ),
        "request_water": (
            "مهمة طلب الماء",
            "تم إنشاء مهمة محلية للمساعدة في توفير الماء. يلزم تدخل الموظف.",
        ),
        "find_water": (
            "مهمة اتجاهات الماء",
            "تم إنشاء مهمة محلية لمعرفة مكان الماء. على الموظف كتابة اتجاهات المكان أدناه.",
        ),
        "please_wait": (
            "تم عرض طلب الانتظار",
            "تم عرض طلب الانتظار للموظف.",
        ),
        "wait_here": (
            "بدأت حالة الانتظار",
            "الشخص ينتظر هنا. يمكن للموظف كتابة رد عندما يكون جاهزًا.",
        ),
        "repeat_missing": (
            "تم طلب التكرار",
            "لا يوجد رد سابق للموظف في هذه الجلسة. على الموظف كتابة الرد مرة أخرى.",
        ),
        "previous_reply": (
            "تم العثور على الرد السابق",
            "آخر رد للموظف: {reply}",
        ),
    },
}


class ReceptionAgent:
    """Runs a small, explicit set of safe reception actions.

    It creates persistent local staff tasks. The UI may separately send a task
    notification through an explicitly configured webhook, but this engine does
    not change bookings or contact interpreter services.
    """

    _LOCAL_TASK_ACTIONS = frozenset(
        {
            "directions",
            "appointment",
            "interpreter",
            "other",
            "request_water",
            "find_water",
        }
    )

    def __init__(self, task_store: TaskStore | None = None) -> None:
        self.task_store = task_store or TaskStore()

    @property
    def pending_tasks(self) -> dict[str, ReceptionTask]:
        return {
            task.id: task
            for task in self.task_store.list_tasks(include_completed=False)
        }

    def execute(
        self,
        option: RequestOption,
        *,
        language: str,
        conversation: Iterable[ConversationTurn],
        input_method: str = "unknown",
        correction_used: bool = False,
        confidence: float | None = None,
    ) -> AgentActionResult:
        if option.id not in ACTION_IDS:
            raise ValueError(f"No agent action is configured for {option.id}")
        if language not in _ACTION_TEXT:
            raise ValueError(f"No agent language is configured for {language}")

        messages = _ACTION_TEXT[language]
        if option.id in {"repeat", "show_again"}:
            previous_reply = next(
                (
                    turn.text
                    for turn in reversed(tuple(conversation))
                    if turn.speaker == "Staff"
                ),
                None,
            )
            if previous_reply:
                title, template = messages["previous_reply"]
                return AgentActionResult(
                    action_id=option.id,
                    title=title,
                    message=template.format(reply=previous_reply),
                    status=AgentActionStatus.COMPLETED,
                    used_conversation_memory=True,
                )
            title, message = messages["repeat_missing"]
            return AgentActionResult(
                action_id=option.id,
                title=title,
                message=message,
                status=AgentActionStatus.WAITING_FOR_STAFF,
            )

        title, message = messages[option.id]
        if option.id in self._LOCAL_TASK_ACTIONS:
            task = self.task_store.create(
                action_id=option.id,
                title=title,
                message=message,
                language=language,
                input_method=input_method,
                correction_used=correction_used,
                confidence=confidence,
            )
            result = AgentActionResult(
                action_id=option.id,
                title=title,
                message=f"{message} [{task.id}]",
                status=AgentActionStatus.LOCAL_TASK,
                task_id=task.id,
            )
            return result

        status = (
            AgentActionStatus.WAITING_FOR_STAFF
            if option.id == "wait_here"
            else AgentActionStatus.COMPLETED
        )
        return AgentActionResult(
            action_id=option.id,
            title=title,
            message=message,
            status=status,
        )

    def complete_tasks(self, task_ids: Iterable[str]) -> int:
        completed = 0
        for task_id in set(task_ids):
            task = self.task_store.get(task_id)
            if task is not None and task.status != TaskStatus.COMPLETED:
                self.task_store.update_status(task_id, TaskStatus.COMPLETED)
                completed += 1
        return completed
