# -*- coding: utf-8  -*-
#
# Copyright (C) 2012-2013 Ben Kurtovic <ben.kurtovic@verizon.net>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from __future__ import print_function, unicode_literals
from os import listdir, path

from mwparserfromhell.compat import py3k
from mwparserfromhell.parser import tokens

class _TestParseError(Exception):
    """Raised internally when a test could not be parsed."""
    pass


class TokenizerTestCase(object):
    """A base test case for tokenizers, whose tests are loaded dynamically.

    Subclassed along with unittest.TestCase to form TestPyTokenizer and
    TestCTokenizer. Tests are loaded dynamically from files in the 'tokenizer'
    directory.
    """

    @classmethod
    def _build_test_method(cls, funcname, data):
        """Create and return a method to be treated as a test case method.

        *data* is a dict containing multiple keys: the *input* text to be
        tokenized, the expected list of tokens as *output*, and an optional
        *label* for the method's docstring.
        """
        def inner(self):
            expected = data["output"]
            actual = self.tokenizer().tokenize(data["input"])
            self.assertEqual(expected, actual)
        if not py3k:
            inner.__name__ = funcname.encode("utf8")
        inner.__doc__ = data["label"]
        return inner

    @classmethod
    def _load_tests(cls, filename, text):
        """Load all tests in *text* from the file *filename*."""
        tests = text.split("\n---\n")
        counter = 1
        digits = len(str(len(tests)))
        for test in tests:
            data = {"name": None, "label": None, "input": None, "output": None}
            try:
                for line in test.strip().splitlines():
                    if line.startswith("name:"):
                        data["name"] = line[len("name:"):].strip()
                    elif line.startswith("label:"):
                        data["label"] = line[len("label:"):].strip()
                    elif line.startswith("input:"):
                        raw = line[len("input:"):].strip()
                        if raw[0] == '"' and raw[-1] == '"':
                            raw = raw[1:-1]
                        raw = raw.encode("raw_unicode_escape")
                        data["input"] = raw.decode("unicode_escape")
                    elif line.startswith("output:"):
                        raw = line[len("output:"):].strip()
                        try:
                            data["output"] = eval(raw, vars(tokens))
                        except Exception as err:
                            raise _TestParseError(err)
            except _TestParseError as err:
                if data["name"]:
                    error = "Could not parse test '{0}' in '{1}':\n\t{2}"
                    print(error.format(data["name"], filename, err))
                else:
                    error = "Could not parse a test in '{0}':\n\t{1}"
                    print(error.format(filename, err))
                continue
            if not data["name"]:
                error = "A test in '{0}' was ignored because it lacked a name"
                print(error.format(filename))
                continue
            if data["input"] is None or data["output"] is None:
                error = "Test '{0}' in '{1}' was ignored because it lacked an input or an output"
                print(error.format(data["name"], filename))
                continue
            number = str(counter).zfill(digits)
            fname = "test_{0}{1}_{2}".format(filename, number, data["name"])
            meth = cls._build_test_method(fname, data)
            setattr(cls, fname, meth)
            counter += 1

    @classmethod
    def build(cls):
        """Load and install all tests from the 'tokenizer' directory."""
        directory = path.join(path.dirname(__file__), "tokenizer")
        extension = ".mwtest"
        for filename in listdir(directory):
            if not filename.endswith(extension):
                continue
            with open(path.join(directory, filename), "r") as fp:
                text = fp.read()
                if not py3k:
                    text = text.decode("utf8")
                cls._load_tests(filename[:0-len(extension)], text)

TokenizerTestCase.build()
