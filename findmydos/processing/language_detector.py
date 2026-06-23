"""
Language detection module for identifying Hebrew text.
"""

import re
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

class LanguageDetector:
    """
    Detects the language of text, with special focus on Hebrew detection.
    """

    def __init__(self):
        """Initialize the language detector."""
        # Hebrew Unicode range
        self.hebrew_pattern = re.compile(r'[֐-׿]')
        # Common Hebrew words for additional verification
        self.hebrew_words = {
            'הפגנה', 'מחאה', 'צה''ל', 'ישראל', 'ירושלים', 'תל אביב',
            'חייל', 'שוטר', 'ממשלה', 'ראשון', 'שני', 'שלישי',
            'רביעי', 'חמישי', 'שישי', 'שבת', 'והנה', 'ויהי',
            'יהיה', 'היה', 'את', 'אתה', 'אתם', 'אתן'
        }

    def detect_language(self, text: str) -> Tuple[str, float]:
        """
        Detect the language of the given text.

        Args:
            text: Text to analyze

        Returns:
            Tuple[str, float]: (language_code, confidence_score)
        """
        if not text or not text.strip():
            return ('unknown', 0.0)

        # Clean the text
        clean_text = text.strip()

        # Check for Hebrew characters
        hebrew_chars = len(self.hebrew_pattern.findall(clean_text))
        total_chars = len([c for c in clean_text if c.isalpha()])

        if total_chars == 0:
            return ('unknown', 0.0)

        hebrew_ratio = hebrew_chars / total_chars if total_chars > 0 else 0

        # Additional check for common Hebrew words
        words = set(re.findall(r'\b\w+\b', clean_text))
        hebrew_word_matches = len(words.intersection(self.hebrew_words))
        hebrew_word_score = min(hebrew_word_matches / 10.0, 1.0)  # Cap at 1.0

        # Combine scores
        if hebrew_ratio > 0.1:  # If more than 10% Hebrew characters
            confidence = min(hebrew_ratio + (hebrew_word_score * 0.3), 1.0)
            return ('hebrew', confidence)
        elif hebrew_word_score > 0.3:  # If we found several Hebrew words
            confidence = min(hebrew_word_score * 0.8, 1.0)
            return ('hebrew', confidence)
        else:
            # Default to English for Latin script with no strong Hebrew indicators
            return ('en', 0.5)

    def is_hebrew(self, text: str, threshold: float = 0.5) -> bool:
        """
        Check if text is primarily in Hebrew.

        Args:
            text: Text to check
            threshold: Confidence threshold for considering text as Hebrew

        Returns:
            bool: True if text is detected as Hebrew with sufficient confidence
        """
        lang, confidence = self.detect_language(text)
        return lang == 'hebrew' and confidence >= threshold