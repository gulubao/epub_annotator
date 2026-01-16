"""EPUB file handling: reading, writing, and CSS injection."""

from pathlib import Path
from typing import Iterator

import ebooklib
from ebooklib import epub


class EpubHandler:
    """Encapsulates ebooklib operations for EPUB manipulation."""

    def __init__(self, input_path: str | Path):
        """Load an EPUB file.

        Args:
            input_path: Path to the EPUB file.
        """
        self.book = epub.read_epub(str(input_path))

    def get_html_items(self) -> Iterator[epub.EpubHtml]:
        """Yield all document items (chapters) from the EPUB.

        Yields:
            EpubHtml items containing chapter content.
        """
        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                yield item

    def add_css(self, css_string: str) -> None:
        """Inject CSS stylesheet into the EPUB.

        Args:
            css_string: CSS content to inject.
        """
        css_item = epub.EpubItem(
            uid="annotation_style",
            file_name="style/annotation.css",
            media_type="text/css",
            content=css_string.encode('utf-8'),
        )
        self.book.add_item(css_item)

        for item in self.book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                item.add_link(
                    href="style/annotation.css",
                    rel="stylesheet",
                    type="text/css",
                )

    def _fix_toc_uids(self) -> None:
        """Ensure all TOC items have valid UIDs (ebooklib bug workaround)."""
        def fix_item(item, idx: int) -> int:
            if isinstance(item, tuple):
                section, children = item
                if hasattr(section, 'uid') and section.uid is None:
                    section.uid = f"nav_{idx}"
                    idx += 1
                for child in children:
                    idx = fix_item(child, idx)
            elif hasattr(item, 'uid') and item.uid is None:
                item.uid = f"nav_{idx}"
                idx += 1
            return idx

        idx = 0
        for item in self.book.toc:
            idx = fix_item(item, idx)

    def save(self, output_path: str | Path) -> None:
        """Write the EPUB to disk.

        Args:
            output_path: Destination path for the modified EPUB.
        """
        self._fix_toc_uids()
        epub.write_epub(str(output_path), self.book)
