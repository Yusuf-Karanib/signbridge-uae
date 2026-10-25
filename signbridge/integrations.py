from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen

from signbridge.config import AGENT_SETTINGS_PATH
from signbridge.tasks import ReceptionTask


@dataclass(frozen=True)
class WebhookSettings:
    enabled: bool = False
    url: str = ""


@dataclass(frozen=True)
class DeliveryResult:
    success: bool
    status_code: int | None
    message: str


class AgentSettingsStore:
    def __init__(self, path: Path | None = AGENT_SETTINGS_PATH) -> None:
        self.path = Path(path) if path is not None else None
        self.load_error: str | None = None
        self.settings = self._load()

    @classmethod
    def in_memory(cls) -> "AgentSettingsStore":
        return cls(path=None)

    def save_webhook(self, *, enabled: bool, url: str) -> WebhookSettings:
        if self.load_error:
            raise RuntimeError(self.load_error)
        clean_url = str(url).strip()
        if enabled:
            validate_webhook_url(clean_url)
        self.settings = WebhookSettings(enabled=bool(enabled), url=clean_url)
        self._save()
        return self.settings

    def clear_webhook(self) -> WebhookSettings:
        return self.save_webhook(enabled=False, url="")

    def _load(self) -> WebhookSettings:
        if self.path is None or not self.path.exists():
            return WebhookSettings()
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict) or not isinstance(payload.get("webhook", {}), dict):
                raise ValueError("Expected saved webhook settings")
            webhook = payload.get("webhook", {})
            return WebhookSettings(
                enabled=bool(webhook.get("enabled", False)),
                url=str(webhook.get("url", "")),
            )
        except (OSError, TypeError, ValueError, json.JSONDecodeError) as exc:
            self.load_error = (
                f"The local connection settings could not be read: {exc}. "
                "They were left untouched so they can be recovered."
            )
            return WebhookSettings()

    def _save(self) -> None:
        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(
                {"version": 1, "webhook": asdict(self.settings)},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        temporary.replace(self.path)


def validate_webhook_url(url: str) -> None:
    parsed = urlparse(str(url).strip())
    if parsed.username or parsed.password:
        raise ValueError("Do not put a username or password inside the webhook URL")
    if not parsed.hostname:
        raise ValueError("Enter a complete webhook URL")
    is_local = parsed.hostname in {"localhost", "127.0.0.1", "::1"}
    if parsed.scheme != "https" and not (parsed.scheme == "http" and is_local):
        raise ValueError("Use an HTTPS webhook URL. HTTP is allowed only for localhost testing")


class StaffWebhookConnector:
    """Sends confirmed local tasks to a Slack/Teams-compatible webhook."""

    def __init__(
        self,
        opener: Callable[..., object] = urlopen,
        timeout_seconds: float = 5.0,
    ) -> None:
        self._opener = opener
        self.timeout_seconds = float(timeout_seconds)

    def send_task(self, task: ReceptionTask, url: str) -> DeliveryResult:
        text = (
            f"SignBridge task {task.id}\n"
            f"{task.title}\n"
            f"{task.message}\n"
            f"Language: {task.language}\n"
            "Open SignBridge Staff desk to accept or complete it."
        )
        return self.send_text(text, url)

    def send_test(self, url: str) -> DeliveryResult:
        return self.send_text(
            "SignBridge connection test. This is not a real assistance request.",
            url,
        )

    def send_text(self, text: str, url: str) -> DeliveryResult:
        validate_webhook_url(url)
        request = Request(
            str(url).strip(),
            data=json.dumps({"text": str(text)}, ensure_ascii=False).encode("utf-8"),
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "User-Agent": "SignBridge-UAE/0.4",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=self.timeout_seconds) as response:
                raw_status = getattr(response, "status", None)
                if raw_status is None:
                    raw_status = response.getcode()
                status = int(raw_status)
            if 200 <= status < 300:
                return DeliveryResult(True, status, "Notification delivered")
            return DeliveryResult(False, status, f"Webhook returned HTTP {status}")
        except HTTPError as exc:
            return DeliveryResult(False, int(exc.code), f"Webhook returned HTTP {exc.code}")
        except (OSError, URLError, TimeoutError, ValueError) as exc:
            return DeliveryResult(False, None, f"Notification failed: {exc}")
