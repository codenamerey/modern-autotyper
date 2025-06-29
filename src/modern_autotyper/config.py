"""Configuration classes for Modern Autotyper."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TypingTask:
    """Configuration for a single typing task."""
    
    keyword: str
    interval: float  # seconds
    count: Optional[int] = None  # None for infinite
    delay_before_start: float = 0.0
    click_x: Optional[int] = None  # Mouse X coordinate to click before typing
    click_y: Optional[int] = None  # Mouse Y coordinate to click before typing
    key_combination: Optional[str] = None  # Key combination to press after typing (e.g., "enter", "ctrl+c")
    
    def __post_init__(self):
        if self.interval <= 0:
            raise ValueError("Interval must be positive")
        if self.count is not None and self.count <= 0:
            raise ValueError("Count must be positive or None")
        if (self.click_x is None) != (self.click_y is None):
            raise ValueError("Both click_x and click_y must be specified together or both None")


@dataclass
class AutoTyperConfig:
    """Configuration for the AutoTyper."""
    
    tasks: List[TypingTask]
    stop_key: str = "esc"
    type_delay: float = 0.05  # delay between characters
    
    def __post_init__(self):
        if not self.tasks:
            raise ValueError("At least one task is required")
        if self.type_delay < 0:
            raise ValueError("Type delay must be non-negative")
