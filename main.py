"""CLI entry point for EPUB annotation.
"""

import argparse
from pathlib import Path

from src.annotator import TextAnnotator
from src.dictionary import ECDictSqlite
from src.difficulty import DifficultyEvaluator
from src.epub_handler import EpubHandler

PROJECT_ROOT = Path(__file__).parent
DEFAULT_DICT_PATH = PROJECT_ROOT / "data" / "stardict.db"

ANNOTATION_CSS = """
.annotated-word { display: inline; }
.annotation {
    font-size: 0.75em;
    color: #7f8c8d;
    background-color: #f0f3f4;
    padding: 0 4px;
    margin: 0 2px;
    border-radius: 4px;
    font-family: sans-serif;
}
"""


def main() -> None:
    """Process EPUB file and inject annotations for difficult words."""
    parser = argparse.ArgumentParser(
        description="Auto-annotate EPUB with definitions for difficult words."
    )
    parser.add_argument("input_file", type=Path, help="Path to input EPUB file")
    parser.add_argument(
        "--output", "-o", type=Path, default=None, help="Path to output EPUB file"
    )
    parser.add_argument(
        "--threshold",
        "-t",
        type=float,
        default=4.0,
        help="Zipf frequency threshold (lower is harder)",
    )
    parser.add_argument(
        "--dict",
        "-d",
        type=Path,
        default=DEFAULT_DICT_PATH,
        help="Path to ECDICT SQLite database",
    )

    args = parser.parse_args()

    input_path: Path = args.input_file
    output_path: Path = args.output or input_path.with_stem(f"{input_path.stem}_annotated")

    print(f"Reading {input_path}...")
    epub_handler = EpubHandler(input_path)

    print(f"Initializing models (wordfreq & ECDICT: {args.dict})...")
    difficulty_model = DifficultyEvaluator(threshold=args.threshold)
    dictionary_service = ECDictSqlite(args.dict)

    annotator = TextAnnotator(difficulty_model, dictionary_service)

    print("Processing chapters...")
    count = 0
    for item in epub_handler.get_html_items():
        original_content = item.get_content()
        new_content = annotator.process_content(original_content)
        item.set_content(new_content)
        count += 1
        print(f"  Processed chapter {count}", end='\r')

    print(f"\nInjecting styles...")
    epub_handler.add_css(ANNOTATION_CSS)

    print(f"Saving to {output_path}...")
    epub_handler.save(output_path)
    print("Done!")


if __name__ == "__main__":
    main()
