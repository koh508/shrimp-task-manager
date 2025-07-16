import unittest
import sys
import os

# Add the root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class SmokeTest(unittest.TestCase):
    def test_import_main_script(self):
        """Ensure the main script can be imported without syntax errors."""
        try:
            import ultra_ai_assistant_unified
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Failed to import ultra_ai_assistant_unified: {e}")

if __name__ == '__main__':
    unittest.main()
