from __future__ import annotations

import unittest

from signbridge.assistance import AssistanceSession, AssistanceStage, REQUEST_OPTIONS
from signbridge.vocabulary import Vocabulary


class AssistanceSessionTests(unittest.TestCase):
    def test_request_cannot_be_sent_before_both_confirmations(self) -> None:
        session = AssistanceSession()

        with self.assertRaises(ValueError):
            session.send_request("en-US")

        session.propose_sign(
            language="asl", label="help", text="Help", confidence=0.91
        )
        self.assertEqual(session.stage, AssistanceStage.CONFIRM_SIGN)
        self.assertEqual(session.turns, [])

        with self.assertRaises(ValueError):
            session.choose_request("hotel_check_in")

        options = session.confirm_sign()
        self.assertEqual(session.stage, AssistanceStage.CHOOSE_REQUEST)
        self.assertIn("hotel_check_in", {option.id for option in options})
        session.choose_request("hotel_check_in")
        self.assertEqual(session.stage, AssistanceStage.CONFIRM_REQUEST)
        self.assertEqual(session.turns, [])

        sent = session.send_request("en-US")
        self.assertEqual(sent.text, "I need help checking in at the hotel.")
        self.assertEqual(session.stage, AssistanceStage.WAITING_REPLY)
        self.assertEqual(len(session.turns), 1)

    def test_complete_clears_temporary_conversation(self) -> None:
        session = AssistanceSession(language="emirati")
        session.propose_sign(
            language="emirati", label="help", text="يساعد", confidence=None
        )
        session.confirm_sign()
        session.choose_request("interpreter")
        session.send_request("ar-AE")
        session.add_staff_reply("سيساعدك أحد الموظفين الآن.", "ar-AE")

        cleared_turns = session.complete()

        self.assertEqual(cleared_turns, 2)
        self.assertEqual(session.stage, AssistanceStage.READY)
        self.assertEqual(session.language, "emirati")
        self.assertEqual(session.turns, [])
        self.assertIsNone(session.proposed_label)
        self.assertIsNone(session.selected_option)

    def test_rejecting_a_prediction_returns_to_ready(self) -> None:
        session = AssistanceSession()
        session.propose_sign(
            language="asl", label="water", text="Water", confidence=0.84
        )

        session.reject_sign()

        self.assertEqual(session.stage, AssistanceStage.READY)
        self.assertIsNone(session.proposed_label)
        self.assertEqual(session.turns, [])

    def test_continue_keeps_conversation_memory_until_completion(self) -> None:
        session = AssistanceSession()
        session.propose_sign(
            language="asl", label="help", text="Help", confidence=0.90
        )
        session.confirm_sign()
        session.choose_request("hotel_service")
        session.send_request("en-US")
        session.add_agent_message("A local hotel service task was created.", "en-US")
        session.add_staff_reply("Hotel staff accepted the request.", "en-US")

        session.continue_conversation()

        self.assertEqual(session.stage, AssistanceStage.READY)
        self.assertEqual(len(session.turns), 3)
        self.assertEqual(session.turns[-1].speaker, "Staff")
        self.assertIsNone(session.selected_option)

        cleared_turns = session.complete()
        self.assertEqual(cleared_turns, 3)
        self.assertEqual(session.turns, [])

    def test_every_current_sign_has_a_guided_request(self) -> None:
        vocabulary = Vocabulary.load()

        for language, pack in vocabulary.packs.items():
            self.assertEqual(set(pack.sign_ids), set(REQUEST_OPTIONS[language]))
            for options in REQUEST_OPTIONS[language].values():
                self.assertTrue(options)
                self.assertTrue(all(option.request_text.strip() for option in options))


if __name__ == "__main__":
    unittest.main()
