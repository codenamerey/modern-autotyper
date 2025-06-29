"""Tests for Modern Autotyper."""

import unittest
import time
import threading
from unittest.mock import Mock, patch

from modern_autotyper.config import TypingTask, AutoTyperConfig
from modern_autotyper.autotyper import AutoTyper


class TestTypingTask(unittest.TestCase):
    """Test TypingTask configuration."""
    
    def test_valid_task(self):
        task = TypingTask("Hello", 1.0)
        self.assertEqual(task.keyword, "Hello")
        self.assertEqual(task.interval, 1.0)
        self.assertIsNone(task.count)
        self.assertEqual(task.delay_before_start, 0.0)
    
    def test_invalid_interval(self):
        with self.assertRaises(ValueError):
            TypingTask("Hello", -1.0)
    
    def test_invalid_count(self):
        with self.assertRaises(ValueError):
            TypingTask("Hello", 1.0, count=-1)


class TestAutoTyperConfig(unittest.TestCase):
    """Test AutoTyperConfig."""
    
    def test_valid_config(self):
        tasks = [TypingTask("Hello", 1.0)]
        config = AutoTyperConfig(tasks)
        self.assertEqual(len(config.tasks), 1)
        self.assertEqual(config.stop_key, "esc")
    
    def test_empty_tasks(self):
        with self.assertRaises(ValueError):
            AutoTyperConfig([])


class TestAutoTyper(unittest.TestCase):
    """Test AutoTyper functionality."""
    
    def setUp(self):
        self.task = TypingTask("Test", 0.1, count=2)
        self.config = AutoTyperConfig([self.task])
    
    @patch('modern_autotyper.autotyper.pyautogui')
    @patch('modern_autotyper.autotyper.keyboard')
    def test_start_stop(self, mock_keyboard, mock_pyautogui):
        autotyper = AutoTyper(self.config)
        
        autotyper.start()
        self.assertTrue(autotyper.running)
        
        time.sleep(0.05)
        autotyper.stop()
        self.assertFalse(autotyper.running)
    
    def test_status(self):
        autotyper = AutoTyper(self.config)
        status = autotyper.status()
        
        self.assertFalse(status["running"])
        self.assertEqual(status["total_tasks"], 1)
        self.assertEqual(status["tasks"][0]["keyword"], "Test")


if __name__ == "__main__":
    unittest.main()
