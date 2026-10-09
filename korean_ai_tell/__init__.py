"""Flag AI tells in Korean (and English) text."""
from .rules import BLOCK, DEFAULT_BASELINE, WARN, Finding, check, lang_of, load_baseline

__all__ = ["BLOCK", "WARN", "DEFAULT_BASELINE", "Finding", "check", "lang_of", "load_baseline"]
__version__ = "0.1.0"
