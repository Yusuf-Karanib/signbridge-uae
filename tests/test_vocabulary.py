import unittest

from signbridge.vocabulary import Vocabulary


class VocabularyTests(unittest.TestCase):
    def test_contains_two_separate_four_sign_language_packs(self) -> None:
        vocabulary = Vocabulary.load()

        self.assertEqual(set(vocabulary.packs), {"asl", "emirati"})
        self.assertEqual(len(vocabulary.pack("asl").signs), 4)
        self.assertEqual(len(vocabulary.pack("emirati").signs), 4)
        self.assertEqual(vocabulary.pack("asl").locale, "en-US")
        self.assertEqual(vocabulary.pack("emirati").locale, "ar-AE")
        self.assertTrue(all(sign.reference_url for sign in vocabulary.pack("asl").signs))
        self.assertTrue(all(sign.reference_url for sign in vocabulary.pack("emirati").signs))
        self.assertEqual(
            set(vocabulary.pack("emirati").sign_ids),
            {"drink", "help", "wait", "repeat"},
        )
        self.assertEqual(
            set(vocabulary.pack("asl").sign_ids),
            {"hello", "help", "water", "again"},
        )


if __name__ == "__main__":
    unittest.main()

