"""Dictionary interface and implementations for word lookup."""

import re
import sqlite3
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional


class BaseDictionary(ABC):
    """Abstract base class for dictionary providers.

    Implementations can connect to SQLite, APIs, or other sources.
    """

    @abstractmethod
    def lookup(self, word: str) -> Optional[str]:
        """Look up a word's definition.

        Args:
            word: The word to look up.

        Returns:
            Definition string if found, None otherwise.
        """
        pass


class SimpleLocalDictionary(BaseDictionary):
    """Simple in-memory dictionary for demonstration.

    Production use: Replace with SQLite/API-backed implementation.
    """

    def __init__(self):
        self._db = {
            "multimodal": "多模态",
            "auxiliary": "辅助的",
            "paradigm": "范式",
            "agnostic": "不可知的",
            "modality": "模态",
            "exploits": "利用",
            "assumption": "假设",
            "underlying": "潜在的",
            "explicit": "明确的",
            "empirically": "经验上",
            "consistently": "一致地",
            "downstream": "下游",
        }

    def lookup(self, word: str) -> Optional[str]:
        """Look up word with basic suffix handling.

        Args:
            word: The word to look up.

        Returns:
            Definition if found, None otherwise.
        """
        base_word = word.lower()

        if base_word in self._db:
            return self._db[base_word]

        # Simple suffix removal for 's'
        if base_word.endswith('s') and base_word[:-1] in self._db:
            return self._db[base_word[:-1]]

        return None


class ECDictSqlite(BaseDictionary):
    """ECDICT SQLite-backed dictionary (3.4M entries).

    Source: https://github.com/skywind3000/ECDICT
    License: MIT
    """

    _LEMMA_PATTERN = re.compile(r'[012]:(\w+)')
    # Pattern to match POS prefix like "n. ", "v. ", "adj. "
    _POS_PATTERN = re.compile(r'^[a-z]{1,4}\.\s*')

    def __init__(self, db_path: str | Path, max_definitions: int = 2,
                 include_phonetic: bool = True):
        """Initialize with path to stardict.db.

        Args:
            db_path: Path to ECDICT SQLite database file.
            max_definitions: Maximum number of definitions to include (default: 2).
            include_phonetic: Whether to include phonetic notation (default: True).
        """
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._max_definitions = max_definitions
        self._include_phonetic = include_phonetic

    def lookup(self, word: str) -> Optional[str]:
        """Look up word in ECDICT.

        Attempts direct lookup first, then tries lemma forms.

        Args:
            word: The word to look up.

        Returns:
            Concise translation with optional phonetic, None if not found.
        """
        cursor = self._conn.cursor()

        # Direct lookup (COLLATE NOCASE handles case)
        cursor.execute(
            "SELECT phonetic, translation, exchange FROM stardict WHERE word = ?",
            (word.lower(),),
        )
        row = cursor.fetchone()

        if row and row['translation']:
            return self._format_result(row['phonetic'], row['translation'])

        # Try lemma lookup via exchange field
        if row and row['exchange']:
            lemma = self._extract_lemma(row['exchange'])
            if lemma:
                cursor.execute(
                    "SELECT phonetic, translation FROM stardict WHERE word = ?",
                    (lemma,),
                )
                lemma_row = cursor.fetchone()
                if lemma_row and lemma_row['translation']:
                    return self._format_result(
                        lemma_row['phonetic'], lemma_row['translation']
                    )

        return None

    def _format_result(self, phonetic: Optional[str],
                       translation: str) -> str:
        """Format the lookup result with phonetic and concise translation.

        Args:
            phonetic: Phonetic notation (may be None).
            translation: Full translation text from database.

        Returns:
            Formatted string: "[phonetic] def1; def2" or just "def1; def2".
        """
        concise = self._extract_translation(translation)

        if self._include_phonetic and phonetic:
            return f"/{phonetic}/ {concise}"
        return concise

    def _extract_translation(self, translation: str) -> str:
        """Extract concise translation (limited definitions).

        Args:
            translation: Full translation text from database.

        Returns:
            Concise translation with at most max_definitions meanings.
        """
        definitions = []

        for line in translation.split('\n'):
            line = line.strip()
            if not line:
                continue

            # Remove POS prefix like "n. " or "vt. "
            line = self._POS_PATTERN.sub('', line)

            # Split by Chinese/English comma or semicolon, take first few
            parts = re.split(r'[,，;；]', line)
            for part in parts:
                part = part.strip()
                if part and part not in definitions:
                    definitions.append(part)
                    if len(definitions) >= self._max_definitions:
                        return '; '.join(definitions)

        return '; '.join(definitions) if definitions else translation.split('\n')[0]

    def _extract_lemma(self, exchange: str) -> Optional[str]:
        """Extract base form from exchange field.

        Exchange format: "p:ran/d:ran/i:running/3:runs/s:runs/0:run"
        0 = lemma, 1 = 3rd person, 2 = past tense, etc.

        Args:
            exchange: Exchange field value.

        Returns:
            Lemma word if found, None otherwise.
        """
        match = self._LEMMA_PATTERN.search(exchange)
        return match.group(1) if match else None

    def close(self) -> None:
        """Close database connection."""
        self._conn.close()
