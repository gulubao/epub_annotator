"""Core annotation logic: HTML parsing and definition injection."""

from bs4 import BeautifulSoup, NavigableString
from typing import Union

from src.dictionary import BaseDictionary
from src.difficulty import DifficultyEvaluator


class TextAnnotator:
    """Processes HTML content to inject word annotations."""

    SKIP_TAGS = frozenset(['script', 'style', 'pre'])

    def __init__(
        self,
        difficulty_model: DifficultyEvaluator,
        dictionary: BaseDictionary,
        wordwise: bool,
    ):
        """
        Args:
            difficulty_model: Evaluator for word difficulty.
            dictionary: Provider for word definitions.
            wordwise: Place annotations on a separate line under each word.
        """
        self.evaluator = difficulty_model
        self.dictionary = dictionary
        self.wordwise = wordwise

    def process_content(self, html_content: bytes) -> bytes:
        """Process HTML content, annotating difficult words.

        Args:
            html_content: Raw HTML bytes from EPUB chapter.

        Returns:
            Modified HTML bytes with annotations injected.
        """
        soup = BeautifulSoup(html_content, 'html.parser')

        for text_node in list(soup.find_all(string=True)):
            if not isinstance(text_node, NavigableString):
                continue

            if text_node.parent.name in self.SKIP_TAGS:
                continue

            text = str(text_node)
            if not text.strip():
                continue

            new_nodes = self._annotate_text(soup, text)
            if new_nodes:
                self._replace_node(text_node, new_nodes)

        return soup.encode(formatter='html')

    def _annotate_text(self, soup: BeautifulSoup, text: str) -> Union[list, None]:
        """Build annotated node list for text.

        Args:
            soup: BeautifulSoup instance for creating new tags.
            text: Text content to annotate.

        Returns:
            List of nodes if modifications made, None otherwise.
        """
        new_nodes = []
        last_idx = 0
        modified = False

        for match in self.evaluator.extract_words(text):
            word = match.group()

            if not self.evaluator.is_difficult(word):
                continue

            definition = self.dictionary.lookup(word)
            if not definition:
                continue

            modified = True

            if match.start() > last_idx:
                new_nodes.append(soup.new_string(text[last_idx:match.start()]))

            if self.wordwise:
                wrapper_tag = "ruby"
                annotation_tag = "rt"
                annotation_text = definition
                wrapper_classes = ["annotated-word", "wordwise"]
            else:
                wrapper_tag = "span"
                annotation_tag = "span"
                annotation_text = f" ({definition})"
                wrapper_classes = ["annotated-word"]

            wrapper = soup.new_tag(wrapper_tag, attrs={"class": wrapper_classes})
            wrapper.string = word

            annotation = soup.new_tag(annotation_tag, attrs={"class": "annotation"})
            annotation.string = annotation_text
            wrapper.append(annotation)

            new_nodes.append(wrapper)
            last_idx = match.end()

        if not modified:
            return None

        if last_idx < len(text):
            new_nodes.append(soup.new_string(text[last_idx:]))

        return new_nodes

    def _replace_node(
        self,
        original_node: NavigableString,
        new_nodes: list,
    ) -> None:
        """Replace a text node with annotated nodes.

        Args:
            original_node: The original NavigableString to replace.
            new_nodes: List of replacement nodes.
        """
        current = original_node
        for node in new_nodes:
            current.insert_after(node)
            current = node
        original_node.extract()
