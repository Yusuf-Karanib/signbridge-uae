from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from signbridge.integrations import (
    AgentSettingsStore,
    StaffWebhookConnector,
    validate_webhook_url,
)
from signbridge.tasks import TaskStore


class FakeResponse:
    status = 200

    def __enter__(self) -> "FakeResponse":
        return self

    def __exit__(self, *_args: object) -> None:
        return None


class IntegrationTests(unittest.TestCase):
    def test_webhook_requires_https_except_for_local_testing(self) -> None:
        validate_webhook_url("https://example.com/signbridge-hook")
        validate_webhook_url("http://127.0.0.1:8080/hook")

        with self.assertRaises(ValueError):
            validate_webhook_url("http://example.com/hook")
        with self.assertRaises(ValueError):
            validate_webhook_url("https://user:secret@example.com/hook")

    def test_settings_are_local_and_persistent(self) -> None:
        with TemporaryDirectory() as temp:
            path = Path(temp) / "settings.json"
            store = AgentSettingsStore(path)
            store.save_webhook(
                enabled=True, url="https://example.com/signbridge-hook"
            )

            loaded = AgentSettingsStore(path)
            self.assertTrue(loaded.settings.enabled)
            self.assertEqual(
                loaded.settings.url, "https://example.com/signbridge-hook"
            )
            loaded.clear_webhook()
            cleared = AgentSettingsStore(path)
            self.assertFalse(cleared.settings.enabled)
            self.assertEqual(cleared.settings.url, "")

    def test_connector_sends_only_a_confirmed_task_summary(self) -> None:
        requests = []

        def opener(request: object, timeout: float) -> FakeResponse:
            requests.append((request, timeout))
            return FakeResponse()

        task = TaskStore.in_memory().create(
            action_id="appointment",
            title="Appointment task",
            message="A local appointment task was created.",
            language="asl",
        )
        connector = StaffWebhookConnector(opener=opener)

        result = connector.send_task(
            task, "https://example.com/signbridge-hook"
        )

        self.assertTrue(result.success)
        self.assertEqual(len(requests), 1)
        request, timeout = requests[0]
        payload = json.loads(request.data.decode("utf-8"))
        self.assertEqual(timeout, 5.0)
        self.assertIn(task.id, payload["text"])
        self.assertNotIn("video", payload["text"].casefold())


if __name__ == "__main__":
    unittest.main()
