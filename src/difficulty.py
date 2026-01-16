"""Difficulty evaluation module using word frequency analysis (Zipf scale)."""

import re
from typing import Iterator

from wordfreq import zipf_frequency


class DifficultyEvaluator:
    """Evaluates word difficulty based on Zipf frequency scale.

    Zipf scale ranges 0-8:
    - ~7.0: Very common words (e.g., "the", "eat")
    - ~4.0: Medium frequency (e.g., "paradigm")
    - ~2.0: Rare words (e.g., "esoteric")
    """

    def __init__(self, lang: str = 'en', threshold: float = 4.5):
        """
        Args:
            lang: Language code for frequency lookup.
            threshold: Zipf frequency threshold. Words below this are "difficult".
                       4.0 ~ top 10,000 words (intermediate learners).
                       3.0 ~ top 30,000 words (advanced learners).
        """
        self.lang = lang
        self.threshold = threshold
        self._word_pattern = re.compile(r'\b[a-zA-Z]{3,}\b')

    def is_difficult(self, word: str) -> bool:
        """Determine if a word is considered difficult.

        Args:
            word: The word to evaluate.

        Returns:
            True if word frequency is above 0 and below threshold.
        """
        if len(word) < 3:
            return False

        freq = zipf_frequency(word.lower(), self.lang)
        return 0 < freq < self.threshold

    def extract_words(self, text: str) -> Iterator[re.Match]:
        """Extract all word matches from text.

        Args:
            text: Input text to scan.

        Yields:
            Match objects for each word found.
        """
        return self._word_pattern.finditer(text)
