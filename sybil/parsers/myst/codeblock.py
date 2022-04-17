import __future__
import re
import textwrap
from typing import Iterable

from sybil import Region, Document, Example
from sybil.parsers.codeblock import CodeBlockParser


CODEBLOCK_START_MYST = re.compile(
    r"((^```python)|(^% invisible-code-block:\s+python)$)",
    re.MULTILINE,
)
CODEBLOCK_END_MYST = re.compile(r"(\n(?=```\n))|((?:% [\S ]*)\n(?=\n))")


class PythonCodeBlockParser(CodeBlockParser):
    """
    A class to instantiate and include when your documentation makes use of
    Python :ref:`codeblock-parser` examples.

    :param future_imports:
        An optional list of strings that will be turned into
        ``from __future__ import ...`` statements and prepended to the code
        in each of the examples found by this parser.
    """

    def __init__(self, future_imports=()):
        super().__init__(language='python')
        self.flags = 0
        for future_import in future_imports:
            self.flags |= getattr(__future__, future_import).compiler_flag

    def __call__(self, document: Document) -> Iterable[Region]:
        for start_match in re.finditer(CODEBLOCK_START_MYST, document.text):
            source_start = start_match.end()
            end_pattern = CODEBLOCK_END_MYST
            end_match = end_pattern.search(document.text, source_start)
            source_end = end_match.end()
            source = textwrap.dedent(document.text[source_start:source_end])
            yield Region(
                start_match.start(),
                source_end,
                source,
                self.evaluate
            )

    def evaluate(self, example: Example) -> None:
        # There must be a nicer way to get line numbers to be correct...
        source = self.pad(example.parsed, example.line)
        source = source.strip().replace("%\n", "\n").replace("% ", "")
        code = compile(
            source, example.path, 'exec', flags=self.flags, dont_inherit=True)
        exec(code, example.namespace)
        # Remove unnecessary __builtins__.
        del example.namespace['__builtins__']
