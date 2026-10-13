from __future__ import annotations

import unittest

from signbridge.agent import ACTION_IDS, AgentActionStatus, ReceptionAgent
from signbridge.assistance import ConversationTurn, REQUEST_OPTIONS, RequestOption
from signbridge.tasks import TaskStore


class ReceptionAgentTests(unittest.TestCase):
    def test_every_request_has_an_agent_action(self) -> None:
        request_ids = {
            option.id
            for language_options in REQUEST_OPTIONS.values()
            for sign_options in language_options.values()
            for option in sign_options
        }

        self.assertEqual(request_ids, set(ACTION_IDS))

    def test_local_task_is_honest_and_can_be_completed(self) -> None:
        agent = ReceptionAgent(TaskStore.in_memory())
        option = RequestOption(
            id="interpreter",
            button_text="Interpreter",
            request_text="I would like an interpreter.",
        )

        result = agent.execute(option, language="asl", conversation=())

        self.assertEqual(result.status, AgentActionStatus.LOCAL_TASK)
        self.assertEqual(result.task_id, "SB-001")
        self.assertFalse(result.external_action_taken)
        self.assertIn("No interpreter service was contacted", result.message)
        self.assertIn("SB-001", agent.pending_tasks)
        self.assertEqual(agent.complete_tasks(["SB-001"]), 1)
        self.assertEqual(agent.pending_tasks, {})

    def test_repeat_action_uses_the_previous_staff_reply(self) -> None:
        agent = ReceptionAgent(TaskStore.in_memory())
        option = RequestOption(
            id="show_again",
            button_text="Show again",
            request_text="Please show that reply again.",
        )
        conversation = (
            ConversationTurn("Signer", "I need directions.", "en-US"),
            ConversationTurn("Staff", "Registration is on the left.", "en-US"),
            ConversationTurn("Signer", option.request_text, "en-US"),
        )

        result = agent.execute(
            option, language="asl", conversation=conversation
        )

        self.assertTrue(result.used_conversation_memory)
        self.assertEqual(result.status, AgentActionStatus.COMPLETED)
        self.assertIn("Registration is on the left", result.message)

    def test_unknown_action_is_rejected(self) -> None:
        agent = ReceptionAgent(TaskStore.in_memory())
        option = RequestOption("unsafe", "Unsafe", "Do something unknown")

        with self.assertRaises(ValueError):
            agent.execute(option, language="asl", conversation=())


if __name__ == "__main__":
    unittest.main()
