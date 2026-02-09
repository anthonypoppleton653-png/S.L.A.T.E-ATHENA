# Modified slate/athena_voice_test.py

import unittest
from typing import Any, Dict, List
from slate.athena_voice import AthenaVoiceConfig, AthenaVoiceInterface

class TestAthenaVoice(unittest.TestCase):

    def setUp(self) -> None:
        """Initialize config and interface for each test."""
        self.config = AthenaVoiceConfig()
        self.interface = AthenaVoiceInterface()

    def tearDown(self) -> None:
        """Clean up config and interface after each test."""
        self.config = None
        self.interface = None

    def test_init_AthenaVoiceConfig(self) -> None:
        """Test initialization of AthenaVoiceConfig with default values."""
        config = AthenaVoiceConfig()
        self.assertIsInstance(config, AthenaVoiceConfig)
        self.assertDictEqual(
            config.to_dict(),
            {"model_name": "default", "max_new_tokens": 50, "temperature": 0.7}
        )

    def test_init_AthenaVoiceInterface(self) -> None:
        """Test initialization of AthenaVoiceInterface with default values."""
        interface = AthenaVoiceInterface()
        self.assertIsInstance(interface, AthenaVoiceInterface)
        self.assertDictEqual(interface.config.to_dict(), {"model_name": "default", "max_new_tokens": 50, "temperature": 0.7})
        self.assertListEqual(interface.conversation_history, [])
        self.assertListEqual(interface.build_queue, [])

    def test_listen_for_input_valid_data(self) -> None:
        """Test listen_for_input method with valid input data."""
        interface = AthenaVoiceInterface()
        input_data: Dict[str, str] = {"text": "Hello, how are you?"}
        interface.listen_for_input(input_data)
        self.assertIn(input_data, interface.conversation_history)

    def test_listen_for_input_invalid_data(self) -> None:
        """Test listen_for_input method with invalid input data."""
        interface = AthenaVoiceInterface()
        invalid_data: Dict[str, Any] = {"invalid_key": "Hello"}
        with self.assertRaises(KeyError):
            interface.listen_for_input(invalid_data)

    def test_process_build_queue_empty(self) -> None:
        """Test process_build_queue method with empty build queue."""
        interface = AthenaVoiceInterface()
        interface.process_build_queue()
        self.assertListEqual(interface.build_queue, [])

    def test_process_build_queue_with_items(self) -> None:
        """Test process_build_queue method with items in the build queue."""
        interface = AthenaVoiceInterface()
        input_data: Dict[str, str] = {"text": "Hello, how are you?"}
        interface.listen_for_input(input_data)
        interface.process_build_queue()
        self.assertIsInstance(interface.build_queue[0], Dict)
        self.assertIn("text", interface.build_queue[0])

    def test_process_input_no_history(self) -> None:
        """Test process_input method with no conversation history."""
        interface = AthenaVoiceInterface()
        input_data: Dict[str, str] = {"text": "Hello, how are you?"}
        interface.process_input(input_data)
        self.assertDictEqual(interface.conversation_history[-1], input_data)

    def test_process_input_with_history(self) -> None:
        """Test process_input method with conversation history."""
        interface = AthenaVoiceInterface()
        input_data_1: Dict[str, str] = {"text": "Hello, how are you?"}
        input_data_2: Dict[str, str] = {"text": "I'm fine, thank you!"}

        interface.process_input(input_data_1)
        interface.process_input(input_data_2)

        expected_history = [input_data_1, input_data_2]
        self.assertListEqual(interface.conversation_history[-len(expected_history):], expected_history)

    def test_process_input_invalid_data(self) -> None:
        """Test process_input method with invalid data."""
        interface = AthenaVoiceInterface()
        invalid_data: Dict[str, Any] = {"invalid_key": "Hello"}
        with self.assertRaises(KeyError):
            interface.process_input(invalid_data)