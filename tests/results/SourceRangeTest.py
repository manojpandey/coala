import unittest
from collections import namedtuple

from coalib.results.SourcePosition import SourcePosition
from coalib.results.SourceRange import SourceRange
from coalib.misc.Constants import COMPLEX_TEST_STRING


class SourceRangeTest(unittest.TestCase):

    def setUp(self):
        self.result_fileA_noline = SourcePosition("A")
        self.result_fileA_line2 = SourcePosition("A", 2)
        self.result_fileB_noline = SourcePosition("B")
        self.result_fileB_line2 = SourcePosition("B", 2)
        self.result_fileB_line4 = SourcePosition("B", 4)

    def test_construction(self):
        uut1 = SourceRange(self.result_fileA_noline)
        self.assertEqual(uut1.end, self.result_fileA_noline)

        uut2 = SourceRange.from_values("A")
        self.assertEqual(uut1, uut2)

        uut = SourceRange.from_values("B", start_line=2, end_line=4)
        self.assertEqual(uut.start, self.result_fileB_line2)
        self.assertEqual(uut.end, self.result_fileB_line4)

    def test_from_clang_range(self):
        # Simulating a clang SourceRange is easier than setting one up without
        # actually parsing a complete C file.
        ClangRange = namedtuple("ClangRange", "start end")
        ClangPosition = namedtuple("ClangPosition", "file line column")
        ClangFile = namedtuple("ClangFile", "name")
        file = ClangFile("t.c")
        start = ClangPosition(file, 1, 2)
        end = ClangPosition(file, 3, 4)

        uut = SourceRange.from_clang_range(ClangRange(start, end))
        compare = SourceRange.from_values("t.c", 1, 2, 3, 4)
        self.assertEqual(uut, compare)

    def test_from_position(self):
        text = "12\n\n3  4"
        uut = SourceRange.from_position("filename", text, 1, 7)
        compare = SourceRange.from_values("filename", 1, 2, 3, 4)
        self.assertEqual(uut, compare)

    def test_file_property(self):
        uut = SourceRange(self.result_fileA_line2)
        self.assertRegex(uut.file, ".*A")

    def test_invalid_arguments(self):
        # arguments must be SourceRanges
        with self.assertRaises(TypeError):
            SourceRange(1, self.result_fileA_noline)

        with self.assertRaises(TypeError):
            SourceRange(self.result_fileA_line2, 1)

    def test_argument_file(self):
        # both Source_Positions should describe the same file
        with self.assertRaises(ValueError):
            SourceRange(self.result_fileA_noline, self.result_fileB_noline)

    def test_argument_order(self):
        # end should come after the start
        with self.assertRaises(ValueError):
            SourceRange(self.result_fileA_line2, self.result_fileA_noline)

    def test_invalid_comparison(self):
        with self.assertRaises(TypeError):
            SourceRange(self.result_fileB_noline, self.result_fileB_line2) < 1

    def test_json(self):
        uut = SourceRange.from_values("B", start_line=2,
                                      end_line=4).__json__(use_relpath=True)
        self.assertEqual(uut['start'], self.result_fileB_line2)


class SourceRangeLineColTest(unittest.TestCase):

    def test_calc_line_col(self):
        # no newlines
        text = "find position of 'z'"
        z_pos = text.find('z')
        self.assertEqual(SourceRange.calc_line_col(text, z_pos), (1, z_pos+1))

        # newline
        text = "find position of\n'z'"
        z_pos = text.find('z')
        self.assertEqual(SourceRange.calc_line_col(text, z_pos), (2, 2))

        # unicode characters
        # tests that each character in the COMPLEX_TEST_STRING is treated as
        # one character and hence would return the correct (line, column)
        text = COMPLEX_TEST_STRING
        for char in text:
            string = char + 'z'
            z_pos = string.find('z')
            if char != '\n':
                self.assertEqual(
                    SourceRange.calc_line_col(string, z_pos), (1, 2))
            else:
                self.assertEqual(
                    SourceRange.calc_line_col(string, z_pos), (2, 1))

        # raw strings
        for raw in [r'a\b', r'a\n', 'a\\n']:
            pos = raw.find(raw[-1])
            self.assertEqual(SourceRange.calc_line_col(text, pos), (1, 3))


class SourceRangeExpandTest(unittest.TestCase):

    def test_expand(self):
        empty_position = SourcePosition("filename")
        file = ["abc\n", "def\n", "ghi\n"]
        empty_range = SourceRange(empty_position, empty_position)
        full_range = SourceRange.from_values("filename", 1, 1, 3, 4)
        self.assertEqual(empty_range.expand(file), full_range)
