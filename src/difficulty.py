"""Difficulty evaluation module using word frequency analysis (Zipf scale)."""

import re
from typing import Iterator

import nltk
from nltk.stem import WordNetLemmatizer
from wordfreq import zipf_frequency

# Ensure WordNet data is available
try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet', quiet=True)


class DifficultyEvaluator:
    """Evaluates word difficulty based on Zipf frequency scale.

    Zipf scale ranges 0-8:
    - ~7.0: Very common words (e.g., "the", "eat")
    - ~4.0: Medium frequency (e.g., "paradigm")
    - ~2.0: Rare words (e.g., "esoteric")
    """

    # WordNet POS tags: n=noun, v=verb, a=adjective, r=adverb
    _POS_TAGS = ('v', 'n', 'a', 'r')

    def __init__(self, lang: str = 'en', threshold: float = 2.5):
        """
        Args:
            lang: Language code for frequency lookup.
            threshold: Zipf frequency threshold. Words below this are "difficult".
                       4.0 ~ top 10,000 words (intermediate learners).
                       3.0 ~ top 30,000 words (advanced learners).
        """
        self.lang = lang
        self.threshold = threshold
        self._lemmatizer = WordNetLemmatizer()
        # Exclude words adjacent to apostrophes (contractions like hadn't, isn't)
        # U+0027 ' U+2018 ' U+2019 ' U+02BC ʼ U+0060 `
        self._word_pattern = re.compile(
            r"(?<![\u0027\u2018\u2019\u02BC\u0060])\b[a-zA-Z]{3,}\b(?![\u0027\u2018\u2019\u02BC\u0060])"
        )

    def _get_max_lemma_freq(self, word: str) -> float:
        """Get maximum frequency across word and its lemma forms.

        Args:
            word: The word to evaluate.

        Returns:
            Maximum Zipf frequency found among original word and lemmas.
        """
        word_lower = word.lower()
        max_freq = zipf_frequency(word_lower, self.lang)

        for pos in self._POS_TAGS:
            lemma = self._lemmatizer.lemmatize(word_lower, pos)
            if lemma != word_lower:
                freq = zipf_frequency(lemma, self.lang)
                if freq > max_freq:
                    max_freq = freq

        return max_freq

    def is_difficult(self, word: str) -> bool:
        """Determine if a word is considered difficult.

        Uses lemmatization to evaluate based on root word frequency,
        preventing simple words with affixes from being marked difficult.

        Args:
            word: The word to evaluate.

        Returns:
            True if max frequency (word or lemma) is above 0 and below threshold.
        """
        if len(word) < 3:
            return False

        freq = self._get_max_lemma_freq(word)
        return 0 < freq < self.threshold

    def extract_words(self, text: str) -> Iterator[re.Match]:
        """Extract all word matches from text.

        Args:
            text: Input text to scan.

        Yields:
            Match objects for each word found.
        """
        return self._word_pattern.finditer(text)
