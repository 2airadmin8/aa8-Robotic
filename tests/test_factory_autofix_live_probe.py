"""Temporary PR #173 live autofix probe. Remove after real end-to-end evidence."""
import unittest

def add_for_autofix_pilot(a: int, b: int) -> int:
    return a - b  # deliberate isolated failing line for AI repair

class TestAutofixPilot(unittest.TestCase):
    def test_add_two_numbers(self):
        self.assertEqual(add_for_autofix_pilot(2, 3), 5)

if __name__ == "__main__":
    unittest.main()

# AA8_AUTO_FIX_ENABLED_VERIFIED: isolated PR173-only retry
