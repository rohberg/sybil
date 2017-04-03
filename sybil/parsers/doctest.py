from __future__ import absolute_import

import re
from doctest import (
    DocTest as BaseDocTest,
    DocTestParser as BaseDocTestParser,
    DocTestRunner as BaseDocTestRunner,
    Example as DocTestExample,
    _unittest_reportflags,
    register_optionflag
)

from ..compat import PY3
from ..region import Region

FIX_BYTE_UNICODE_REPR = register_optionflag('FIX_BYTE_UNICODE_REPR')
BYTE_LITERAL = re.compile(r"b((['\"])[^\2]*\2)", re.MULTILINE)
UNICODE_LITERAL = re.compile(r"u((['\"])[^\2]*\2)", re.MULTILINE)


class DocTest(BaseDocTest):
    def __init__(self, examples, globs, name, filename, lineno, docstring):
        # do everything like regular doctests, but don't make a copy of globs
        BaseDocTest.__init__(self, examples, globs, name, filename, lineno,
            docstring)
        self.globs = globs


class DocTestRunner(BaseDocTestRunner):

    def __init__(self, optionflags=0):
        optionflags |= _unittest_reportflags
        BaseDocTestRunner.__init__(self, verbose=False, optionflags=optionflags)

    def _failure_header(self, test, example):
        return ''


def fix_byte_unicode_repr(want):
    if PY3:
        pattern = UNICODE_LITERAL
    else:
        pattern = BYTE_LITERAL
    return pattern.sub(r"\1", want)


class DocTestParser(BaseDocTestParser):

    def __init__(self, optionflags=0):
        self.runner = DocTestRunner(optionflags=optionflags)

    def __call__(self, document):
        # a cut down version of doctest.DocTestParser.parse:

        text = document.text.expandtabs()
        # If all lines begin with the same indentation, then strip it.
        min_indent = self._min_indent(text)
        if min_indent > 0:
            text = '\n'.join([l[min_indent:] for l in text.split('\n')])

        charno, lineno = 0, 0
        # Find all doctest examples in the string:
        for m in self._EXAMPLE_RE.finditer(text):
            # Update lineno (lines before this example)
            lineno += text.count('\n', charno, m.start())
            # Extract info from the regexp match.
            (source, options, want, exc_msg) = \
                     self._parse_example(m, document.path, lineno)

            if self.runner.optionflags & FIX_BYTE_UNICODE_REPR:
                want = fix_byte_unicode_repr(want)

            # Create an Example, and add it to the list.
            if not self._IS_BLANK_OR_COMMENT(source):
                yield Region(
                    m.start(),
                    m.end(),
                    DocTestExample(source, want, exc_msg,
                            lineno=lineno,
                            indent=min_indent+len(m.group('indent')),
                            options=options),
                    self.evaluate

                )
            # Update lineno (lines inside this example)
            lineno += text.count('\n', m.start(), m.end())
            # Update charno.
            charno = m.end()

    def evaluate(self, example, namespace):
        output = []
        self.runner.run(
            DocTest([example], namespace, name=None,
                    filename=None, lineno=example.lineno, docstring=None),
            clear_globs=False,
            out=output.append
        )
        return ''.join(output)
