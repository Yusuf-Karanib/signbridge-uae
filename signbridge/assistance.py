from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AssistanceStage(str, Enum):
    READY = "ready"
    CONFIRM_SIGN = "confirm_sign"
    CHOOSE_REQUEST = "choose_request"
    CONFIRM_REQUEST = "confirm_request"
    WAITING_REPLY = "waiting_reply"


@dataclass(frozen=True)
class RequestOption:
    id: str
    button_text: str
    request_text: str


@dataclass(frozen=True)
class ConversationTurn:
    speaker: str
    text: str
    locale: str


COMPETITION_ACTION_IDS = frozenset(
    {"directions", "appointment", "interpreter"}
)


REQUEST_OPTIONS: dict[str, dict[str, tuple[RequestOption, ...]]] = {
    "asl": {
        "hello": (
            RequestOption("start", "Start assistance", "Hello. I need assistance."),
        ),
        "help": (
            RequestOption("directions", "Directions", "I need help with directions."),
            RequestOption("appointment", "Appointment", "I need help with an appointment."),
            RequestOption(
                "interpreter",
                "Sign-language interpreter",
                "I would like a sign-language interpreter.",
            ),
            RequestOption("other", "Other help", "I need assistance."),
        ),
        "water": (
            RequestOption("request_water", "Request water", "I would like some water."),
            RequestOption(
                "find_water", "Find drinking water", "Where can I get drinking water?"
            ),
        ),
        "again": (
            RequestOption("repeat", "Ask staff to repeat", "Please repeat that."),
            RequestOption(
                "show_again", "Show the last reply again", "Please show that reply again."
            ),
        ),
    },
    "emirati": {
        "drink": (
            RequestOption("request_water", "أريد ماءً", "أريد بعض الماء، من فضلك."),
            RequestOption("find_water", "أين الماء؟", "أين يمكنني الحصول على ماء للشرب؟"),
        ),
        "help": (
            RequestOption("directions", "الاتجاهات", "أحتاج إلى مساعدة في معرفة الاتجاهات."),
            RequestOption("appointment", "موعد", "أحتاج إلى مساعدة بخصوص موعد."),
            RequestOption(
                "interpreter",
                "مترجم لغة إشارة",
                "أرغب في طلب مترجم لغة إشارة.",
            ),
            RequestOption("other", "مساعدة أخرى", "أحتاج إلى مساعدة، من فضلك."),
        ),
        "wait": (
            RequestOption("please_wait", "اطلب من الموظف الانتظار", "من فضلك انتظر قليلاً."),
            RequestOption("wait_here", "سأنتظر هنا", "سأنتظر هنا."),
        ),
        "repeat": (
            RequestOption("repeat", "اطلب التكرار", "من فضلك أعد ذلك."),
            RequestOption("show_again", "اعرض الرد مرة أخرى", "من فضلك اعرض الرد مرة أخرى."),
        ),
    },
}


class AssistanceSession:
    """A temporary, confirmation-first communication workflow.

    It deliberately contains no model or language-model logic. The camera model proposes
    a sign, but this state machine prevents a request from being sent before the person
    confirms both the sign and the intended follow-up request.
    """

    def __init__(self, language: str = "asl") -> None:
        self.language = language
        self.stage = AssistanceStage.READY
        self.proposed_label: str | None = None
        self.proposed_text: str | None = None
        self.proposed_confidence: float | None = None
        self.selected_option: RequestOption | None = None
        self.turns: list[ConversationTurn] = []

    def reset(self, language: str | None = None) -> None:
        if language is not None:
            self.language = language
        self.stage = AssistanceStage.READY
        self.proposed_label = None
        self.proposed_text = None
        self.proposed_confidence = None
        self.selected_option = None
        self.turns.clear()

    def propose_sign(
        self,
        *,
        language: str,
        label: str,
        text: str,
        confidence: float | None,
    ) -> None:
        if label not in REQUEST_OPTIONS.get(language, {}):
            raise ValueError(f"No guided request is configured for {language}:{label}")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        self.language = language
        self.proposed_label = label
        self.proposed_text = text
        self.proposed_confidence = confidence
        self.selected_option = None
        self.stage = AssistanceStage.CONFIRM_SIGN

    def reject_sign(self) -> None:
        if self.stage != AssistanceStage.CONFIRM_SIGN:
            raise ValueError("There is no proposed sign to reject")
        self.proposed_label = None
        self.proposed_text = None
        self.proposed_confidence = None
        self.selected_option = None
        self.stage = AssistanceStage.READY

    def confirm_sign(self) -> tuple[RequestOption, ...]:
        if self.stage != AssistanceStage.CONFIRM_SIGN or self.proposed_label is None:
            raise ValueError("A proposed sign must be confirmed first")
        options = REQUEST_OPTIONS[self.language][self.proposed_label]
        self.stage = AssistanceStage.CHOOSE_REQUEST
        return options

    def available_options(
        self, allowed_ids: frozenset[str] | set[str] | None = None
    ) -> tuple[RequestOption, ...]:
        if self.proposed_label is None:
            return ()
        options = REQUEST_OPTIONS.get(self.language, {}).get(self.proposed_label, ())
        if allowed_ids is None:
            return options
        return tuple(option for option in options if option.id in allowed_ids)

    def choose_request(
        self,
        option_id: str,
        allowed_ids: frozenset[str] | set[str] | None = None,
    ) -> RequestOption:
        if self.stage != AssistanceStage.CHOOSE_REQUEST:
            raise ValueError("Confirm the sign before choosing a request")
        option = next(
            (
                item
                for item in self.available_options(allowed_ids)
                if item.id == option_id
            ),
            None,
        )
        if option is None:
            raise ValueError("That request is not available for this sign")
        self.selected_option = option
        self.stage = AssistanceStage.CONFIRM_REQUEST
        return option

    def change_request(self) -> None:
        if self.stage != AssistanceStage.CONFIRM_REQUEST:
            raise ValueError("There is no selected request to change")
        self.selected_option = None
        self.stage = AssistanceStage.CHOOSE_REQUEST

    def send_request(self, locale: str) -> ConversationTurn:
        if self.stage != AssistanceStage.CONFIRM_REQUEST or self.selected_option is None:
            raise ValueError("The request must be selected and confirmed before it is sent")
        turn = ConversationTurn(
            speaker="Signer",
            text=self.selected_option.request_text,
            locale=locale,
        )
        self.turns.append(turn)
        self.stage = AssistanceStage.WAITING_REPLY
        return turn

    def add_staff_reply(self, text: str, locale: str) -> ConversationTurn:
        if self.stage != AssistanceStage.WAITING_REPLY:
            raise ValueError("Send a confirmed request before adding a staff reply")
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("Enter the staff reply first")
        turn = ConversationTurn(speaker="Staff", text=clean_text, locale=locale)
        self.turns.append(turn)
        return turn

    def add_agent_message(self, text: str, locale: str) -> ConversationTurn:
        if self.stage != AssistanceStage.WAITING_REPLY:
            raise ValueError("Send a confirmed request before running an agent action")
        clean_text = text.strip()
        if not clean_text:
            raise ValueError("The agent action returned an empty message")
        turn = ConversationTurn(speaker="Agent", text=clean_text, locale=locale)
        self.turns.append(turn)
        return turn

    def continue_conversation(self) -> None:
        if self.stage != AssistanceStage.WAITING_REPLY:
            raise ValueError("Finish the current request before continuing")
        self.proposed_label = None
        self.proposed_text = None
        self.proposed_confidence = None
        self.selected_option = None
        self.stage = AssistanceStage.READY

    def complete(self) -> int:
        if not self.turns or self.stage not in (
            AssistanceStage.READY,
            AssistanceStage.WAITING_REPLY,
        ):
            raise ValueError("A confirmed request must be sent before completing the session")
        turn_count = len(self.turns)
        self.reset()
        return turn_count
