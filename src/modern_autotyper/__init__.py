"""Modern Autotyper - Multi-threaded autotyper with configurable intervals."""

__version__ = "1.0.0"
__author__ = "Ryan"

from .autotyper import AutoTyper
from .config import AutoTyperConfig, TypingTask

# GUI is optional import
try:
    from .gui import AutoTyperApp
    __all__ = ["AutoTyper", "AutoTyperConfig", "TypingTask", "AutoTyperApp"]
except ImportError:
    __all__ = ["AutoTyper", "AutoTyperConfig", "TypingTask"]
