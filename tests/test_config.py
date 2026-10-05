import unittest

from signbridge.config import RECOMMENDED_SAMPLES_PER_CLASS


class ConfigTests(unittest.TestCase):
    def test_current_prototype_target_is_thirty_samples_per_class(self) -> None:
        self.assertEqual(RECOMMENDED_SAMPLES_PER_CLASS, 30)


if __name__ == "__main__":
    unittest.main()
