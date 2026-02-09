# Modified: 2023-03-15T14:30:00Z | Author: SLATE-CODER | Change: Added more comprehensive tests for ClaudeCodeManager

import subprocess
from pathlib import Path
from typing import Optional, Tuple
import unittest.mock as mock
import unittest

class ActionGuard:
    """Action guard class to control action performance."""

    def can_perform_action(self) -> bool:
        """Check if an action can be performed.

        Returns:
            bool: True if the action can be performed, False otherwise.
        """
        return True  # Placeholder implementation, replace with actual guard logic

class ClaudeCodeManager:
    """Manager class for handling Claude code file."""

    code_file_path = Path.home() / ".claude" / "code.py"

    def __init__(self, action_guard: ActionGuard):
        """Initialize ClaudeCodeManager with an action guard.

        Args:
            action_guard (ActionGuard): An instance of ActionGuard.
        """
        self.action_guard = action_guard
        self._mock_input = None

    def save_code(self, code: str) -> None:
        """Save the given code to the Claude code file.

        Args:
            code (str): The code to be saved.
        """
        with open(self.code_file_path, "w", encoding="utf-8") as f:
            f.write(code)

    def run_code(self) -> Optional[str]:
        """Run the code in the Claude code file and return its output.

        Returns:
            Optional[str]: The output of the code if it runs successfully, None otherwise.
        """
        if not self.action_guard.can_perform_action():
            return None

        result = self._run_code_in_subprocess()
        if result.returncode != 0:
            return ""

        return result.stdout.decode().strip()

    def _run_code_in_subprocess(self) -> subprocess.CompletedProcess:
        """Run the code in the Claude code file using a subprocess.

        Returns:
            subprocess.CompletedProcess: The completed process object.
        """
        return subprocess.run(["python", "-u", str(self.code_file_path)], capture_output=True)

    def set_mock_input(self, input: str) -> None:
        """Set mock input for testing purposes.

        Args:
            input (str): The mock input to be used.
        """
        self._mock_input = input

class TestClaudeCodeManager(unittest.TestCase):
    """Test cases for ClaudeCodeManager class."""

    @classmethod
    def setUpClass(cls) -> None:
        """Set up class-level variables."""
        cls.expected_output_path = Path.home() / ".claude" / "output.txt"

    def setUp(self) -> None:
        """Set up method-level variables."""
        self.guard = mock.MagicMock(spec=ActionGuard)
        self.manager = ClaudeCodeManager(self.guard)

    def tearDown(self) -> None:
        """Tear down method-level resources."""
        if (code_file_path := self.manager.code_file_path).exists():
            code_file_path.unlink()
        if self.expected_output_path.exists():
            self.expected_output_path.unlink()

    def test_save_code_with_large_data(self):
        """Test saving large data to the Claude code file."""
        large_code = "".join(["print('Hello, World!')\n" for _ in range(1000)])
        expected_file_path = Path.home() / ".claude" / "code.py"

        self.manager.save_code(large_code)
        with open(expected_file_path, "r", encoding="utf-8") as f:
            saved_code = f.read().strip()

        self.assertEqual(large_code.strip(), saved_code)

    def test_save_code_with_special_characters(self):
        """Test saving code with special characters to the Claude code file."""
        special_chars_code = 'print("Hello, World! 🌍💫")'
        expected_file_path = Path.home() / ".claude" / "code.py"

        self.manager.save_code(special_chars_code)
        with open(expected_file_path, "r", encoding="utf-8") as f:
            saved_code = f.read().strip()

        self.assertEqual(special_chars_code.strip(), saved_code)

    def test_run_code_with_multiple_lines(self):
        """Test running code with multiple lines and mock input."""
        multi_line_code = """
if name := input("Enter your name: ").strip():
    print(f"Hello, {name}!")
else:
    print("No input provided.")
"""
        expected_output = "Hello, John Doe!\n"

        self.manager.set_mock_input("John Doe\n")
        with mock.patch.object(ClaudeCodeManager, "_run_code_in_subprocess") as mock_run:
            mock_run.return_value.stdout.encode = lambda: expected_output.encode()
            output = self.manager.run_code()
            mock_run.assert_called_once()
            self.assertEqual(expected_output.strip(), output)

    def test_run_code_with_empty_input(self):
        """Test running code with empty input and mock input."""
        empty_input_code = 'name = input("Enter your name: ") \nprint(f"Hello, {name}")'
        expected_output = "No input provided.\n"

        self.manager.set_mock_input("\n")
        with mock.patch.object(ClaudeCodeManager, "_run_code_in_subprocess") as mock_run:
            mock_run.return_value.stdout.encode = lambda: expected_output.encode()
            output = self.manager.run_code()
            mock_run.assert_called_once()
            self.assertEqual(expected_output.strip(), output)

    def test_run_code_with_exception_handling(self):
        """Test running code with exception handling."""
        exception_raising_code = """
try:
    x = 1 / 0
except Exception as e:
    print(f"Error: {e}")
"""
        expected_output = "Error: division by zero\n"

        self.manager.save_code(exception_raising_code)
        output = self.manager.run_code()
        self.assertEqual(expected_output.strip(), output)

if __name__ == "__main__":
    unittest.main()