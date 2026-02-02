"""
Text input processing and sanitization.
Handles query preprocessing and safety checks.
"""

import re
from typing import List, Optional, Tuple

from pydantic import BaseModel


class ProcessedQuery(BaseModel):
    """Result of text processing."""
    original: str
    cleaned: str
    intent_keywords: List[str] = []
    is_safe: bool = True
    safety_message: Optional[str] = None


class TextProcessor:
    """
    Process and sanitize text input.
    Handles cleaning, safety checks, and keyword extraction.
    """

    # Keywords that indicate potential harmful queries
    HARMFUL_PATTERNS = [
        r"how\s+to\s+(starve|purge|vomit)",
        r"(anorexia|bulimia)\s+(tips|tricks|how)",
        r"(extreme|crash|dangerous)\s+diet",
        r"lose\s+\d+\s+pounds?\s+in\s+(\d|one|two|three)\s+(day|week)",
        r"(steroids?|ped|performance.enhancing)",
        r"(laxative|diuretic)\s+(abuse|for.weight)",
    ]

    # Fitness/nutrition intent keywords
    INTENT_KEYWORDS = {
        "workout": ["workout", "exercise", "training", "gym", "lift", "strength", "cardio"],
        "nutrition": ["food", "meal", "eat", "diet", "nutrition", "calories", "protein", "carbs", "fat"],
        "sleep": ["sleep", "rest", "recovery", "tired", "fatigue", "energy"],
        "weight": ["weight", "lose", "gain", "bulk", "cut", "body"],
        "plan": ["plan", "schedule", "routine", "program", "week"],
        "injury": ["injury", "pain", "hurt", "sore", "strain"]
    }

    def __init__(self, max_length: int = 1000):
        """
        Initialize text processor.

        Args:
            max_length: Maximum query length in characters.
        """
        self.max_length = max_length
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.harmful_regex = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.HARMFUL_PATTERNS
        ]

    def process(self, text: str) -> ProcessedQuery:
        """
        Process and validate text input.

        Args:
            text: Raw input text.

        Returns:
            ProcessedQuery with cleaned text and metadata.
        """
        original = text

        # Clean the text
        cleaned = self._clean(text)

        # Safety check
        is_safe, safety_message = self._check_safety(cleaned)

        # Extract intent keywords
        intent_keywords = self._extract_intents(cleaned)

        return ProcessedQuery(
            original=original,
            cleaned=cleaned,
            intent_keywords=intent_keywords,
            is_safe=is_safe,
            safety_message=safety_message
        )

    def _clean(self, text: str) -> str:
        """
        Clean and normalize text.

        Args:
            text: Raw text.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        # Strip whitespace
        text = text.strip()

        # Truncate if too long
        if len(text) > self.max_length:
            text = text[:self.max_length]

        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)

        # Remove potentially harmful characters but keep unicode
        text = re.sub(r'[<>{}[\]\\]', '', text)

        return text

    def _check_safety(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Check if query is safe to process.

        Args:
            text: Cleaned text.

        Returns:
            Tuple of (is_safe, message).
        """
        text_lower = text.lower()

        for pattern in self.harmful_regex:
            if pattern.search(text_lower):
                return False, (
                    "This query appears to be asking about potentially harmful practices. "
                    "Please consult a healthcare professional for guidance on safe approaches."
                )

        return True, None

    def _extract_intents(self, text: str) -> List[str]:
        """
        Extract intent categories from text.

        Args:
            text: Cleaned text.

        Returns:
            List of detected intent categories.
        """
        text_lower = text.lower()
        detected = []

        for intent, keywords in self.INTENT_KEYWORDS.items():
            if any(kw in text_lower for kw in keywords):
                detected.append(intent)

        return detected

    def is_empty_or_whitespace(self, text: str) -> bool:
        """
        Check if text is empty or whitespace only.

        Args:
            text: Input text.

        Returns:
            True if empty or whitespace only.
        """
        return not text or not text.strip()

    def extract_numbers(self, text: str) -> List[float]:
        """
        Extract numeric values from text.

        Args:
            text: Input text.

        Returns:
            List of numbers found.
        """
        pattern = r'(\d+\.?\d*)'
        matches = re.findall(pattern, text)
        return [float(m) for m in matches]

    def extract_foods(self, text: str) -> List[str]:
        """
        Extract potential food mentions from text.

        Args:
            text: Input text.

        Returns:
            List of potential food items.
        """
        # Common food words to look for
        food_indicators = [
            "ate", "eat", "eating", "had", "have", "cooked",
            "made", "breakfast", "lunch", "dinner", "snack"
        ]

        words = text.lower().split()
        foods = []

        # Look for words after food indicator words
        for i, word in enumerate(words):
            if word in food_indicators and i + 1 < len(words):
                # Collect next few words as potential food
                potential_food = " ".join(words[i+1:i+4])
                # Clean up
                potential_food = re.sub(r'[^\w\s]', '', potential_food)
                if potential_food:
                    foods.append(potential_food.strip())

        return foods
