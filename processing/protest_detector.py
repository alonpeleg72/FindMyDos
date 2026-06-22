"""
Protest detection module for identifying protest-related content,
with specific focus on Hasidic/Haredi community protests.
"""

import re
import logging
from typing import Tuple, List
from .language_detector import LanguageDetector

logger = logging.getLogger(__name__)

class ProtestDetector:
    """
    Detects whether text content is related to protests,
    with special attention to Hasidic/Haredi community protests.
    """

    def __init__(self):
        """Initialize the protest detector."""
        self.language_detector = LanguageDetector()

        # Protest-related keywords in Hebrew
        self.hebrew_protest_keywords = {
            'הפגנה', 'מחאה', 'צעדה', 'שביתה', 'פקודה',
            'תהלוכת', 'כנס חירום', 'עצרת', 'מחסום', 'צומת',
            'חסימה', 'שיבוש', 'הפרעה', 'דשא', 'כיכר',
            'רחוב', 'שדרות', 'כביש', 'צומת', 'מעבר'
        }

        # Hasidic/Haredi community identifiers in Hebrew
        self.hebrew_hasidic_keywords = {
            'חסידי', 'חרדי', 'ברסלב', 'גUR', 'ויזhnitz',
            'חב''ד', 'חזון איש', 'פוניבז', 'מיר', 'בעלז',
            'סאטמר', 'קופיטשינר', 'תולדות אהרן',
            'שומרי חומות', 'קהילה', 'עדה', 'ציבור',
            'מגזר', 'ליטאי', 'ספרדי', 'אשכנזי'
        }

        # Location indicators that often appear in protest reports
        self.location_indicators = {
            'בירושלים', 'בתל אביב', 'בחיפה', 'בבני ברק',
            'במחנה יהודה', 'בשכונה', 'בשכונת', ' ברחוב ',
            ' בצומת ', ' בכניסה ', ' ביציאה ', ' בכיכר '
        }

        # English protest keywords (for bilingual content)
        self.english_protest_keywords = {
            'protest', 'demonstration', 'march', 'strike', 'rally',
            'demonstrators', 'protesters', 'assembly', 'gathering',
            'road block', 'street closure', 'traffic disruption'
        }

    def detect_protest(self, text: str) -> Tuple[bool, float, dict]:
        """
        Detect if text is related to a protest, with confidence score.

        Args:
            text: Text to analyze

        Returns:
            Tuple[bool, float, dict]:
                (is_protest, confidence_score, metadata)
                metadata includes: has_hebrew, has_hasidic, location_indicators_found
        """
        if not text or not text.strip():
            return (False, 0.0, {})

        # Detect language
        lang, lang_confidence = self.language_detector.detect_language(text)
        is_hebrew = lang == 'hebrew'

        # Convert to lowercase for matching
        text_lower = text.lower()

        # Count Hebrew protest keywords
        hebrew_protest_matches = sum(
            1 for keyword in self.hebrew_protest_keywords
            if keyword in text
        )

        # Count Hasidic/Haredi identifiers
        hasidic_matches = sum(
            1 for keyword in self.hebrew_hasidic_keywords
            if keyword in text
        )

        # Count English protest keywords
        english_protest_matches = sum(
            1 for keyword in self.english_protest_keywords
            if keyword in text_lower
        )

        # Count location indicators
        location_matches = sum(
            1 for indicator in self.location_indicators
            if indicator in text
        )

        # Calculate scores
        protest_score = 0.0
        hasidic_score = 0.0

        # Protest score based on keyword matches
        if hebrew_protest_matches > 0:
            protest_score += min(hebrew_protest_matches * 0.2, 0.6)  # Max 0.6 from Hebrew
        if english_protest_matches > 0:
            protest_score += min(english_protest_matches * 0.15, 0.4)  # Max 0.4 from English

        # Hasidic score
        if hasidic_matches > 0:
            hasidic_score = min(hasidic_matches * 0.25, 1.0)  # Max 1.0 from Hasidic keywords

        # Boost score if both protest and Hasidic indicators are present
        if protest_score > 0 and hasidic_score > 0:
            protest_score = min(protest_score * 1.3, 1.0)  # 30% boost, capped at 1.0

        # Location indicators add confidence
        if location_matches > 0:
            protest_score = min(protest_score + (location_matches * 0.1), 1.0)

        # Language bonus - Hebrew text gets a slight boost for protest detection in Israel context
        if is_hebrew:
            protest_score = min(protest_score + 0.1, 1.0)

        # Determine if this is a protest
        is_protest = protest_score >= 0.4  # Threshold for considering it a protest

        # Prepare metadata
        metadata = {
            'has_hebrew': is_hebrew,
            'hebrew_confidence': lang_confidence if is_hebrew else 0.0,
            'has_hasidic': hasidic_score > 0.3,
            'hasidic_matches': hasidic_matches,
            'protest_keyword_matches': hebrew_protest_matches + english_protest_matches,
            'location_indicators_found': location_matches > 0,
            'location_match_count': location_matches
        }

        return (is_protest, protest_score, metadata)

    def is_hasidic_protest(self, text: str) -> Tuple[bool, float]:
        """
        Specifically check if text is related to a Hasidic/Haredi protest.

        Args:
            text: Text to analyze

        Returns:
            Tuple[bool, float]: (is_hasidic_protest, confidence_score)
        """
        is_protest, protest_confidence, metadata = self.detect_protest(text)

        if not is_protest:
            return (False, 0.0)

        # Check if it has strong Hasidic indicators
        hasidic_confidence = min(metadata.get('hasidic_matches', 0) * 0.25, 1.0)
        is_hasidic = metadata.get('has_hasidic', False)

        # Combined confidence: protest confidence * Hasidic confidence
        combined_confidence = protest_confidence * hasidic_confidence if is_hasidic else 0.0

        return (is_hasidic, combined_confidence)