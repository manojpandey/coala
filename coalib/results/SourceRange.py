from os.path import relpath

from coalib.misc.Decorators import enforce_signature, get_public_members
from coalib.results.SourcePosition import SourcePosition
from coalib.results.TextRange import TextRange


class SourceRange(TextRange):

    @enforce_signature
    def __init__(self,
                 start: SourcePosition,
                 end: (SourcePosition, None)=None,
                 text=None,
                 start_position=None,
                 end_position=None):
        """
        Creates a new SourceRange.

        :param start:       A SourcePosition indicating the start of the range.
        :param end:         A SourcePosition indicating the end of the range.
                            If ``None`` is given, the start object will be used
                            here. end must be in the same file and be greater
                            than start as negative ranges are not allowed.
        :raises TypeError:  Raised when
                            - start is no SourcePosition or None.
                            - end is no SourcePosition.
        :raises ValueError: Raised when file of start and end mismatch.
        """
        TextRange.__init__(self, start, end)

        if self.start.file != self.end.file:
            raise ValueError("File of start and end position do not match.")

        self.text = text
        self.start_position = start_position
        self.end_position = end_position

    @classmethod
    def from_values(cls,
                    file,
                    start_line=None,
                    start_column=None,
                    end_line=None,
                    end_column=None):
        start = SourcePosition(file, start_line, start_column)
        if not end_line:
            end = None
        else:
            end = SourcePosition(file, end_line, end_column)

        return cls(start, end)

    @classmethod
    def from_clang_range(cls, range):
        """
        Creates a SourceRange from a clang SourceRange object.

        :param range: A cindex.SourceRange object.
        """
        return cls.from_values(range.start.file.name,
                               range.start.line,
                               range.start.column,
                               range.end.line,
                               range.end.column)

    @classmethod
    def from_position(cls, filename, text, start_position, end_position):
        start_line, start_column = cls.calc_line_col(text, start_position)
        end_line, end_column = cls.calc_line_col(text, end_position)
        return cls(SourcePosition(filename, start_line, start_column),
                   SourcePosition(filename, end_line, end_column),
                   text=text,
                   start_position=start_position,
                   end_position=end_position)

    @property
    def file(self):
        return self.start.file

    @property
    def position(self):
        if self.text is not None:
            return self.start_position, self.end_position

        else:
            return None

    @classmethod
    def calc_line_col(cls, text, pos_to_find):
        """
        Calculate line number and column in the text, from position.
        Uses \\n as the newline character. Lines and columns start from 1.

        :param text:        A string with all the contents of file.
        :param pos_to_find: position of character to be found in the
                            line,column form.

        :return:            a tuple of the form (line, column).
        """
        line = 1
        pos = -1
        pos_new_line = text.find('\n')
        while True:
            if pos_new_line == -1:
                return (line, pos_to_find - pos)

            if pos_to_find <= pos_new_line:
                return (line, pos_to_find - pos)

            else:
                line += 1
                pos = pos_new_line
                pos_new_line = text.find('\n', pos_new_line + 1)

    def expand(self, file_contents):
        """
        Passes a new SourceRange that covers the same area of a file as this
        one would. All values of None get replaced with absolute values.

        values of None will be interpreted as follows:
        self.start.line is None:   -> 1
        self.start.column is None: -> 1
        self.end.line is None:     -> last line of file
        self.end.column is None:   -> last column of self.end.line

        :param file_contents: File contents of the applicable file
        :return:              TextRange with absolute values
        """
        tr = TextRange.expand(self, file_contents)

        return SourceRange.from_values(self.file,
                                       tr.start.line,
                                       tr.start.column,
                                       tr.end.line,
                                       tr.end.column)

    def __json__(self, use_relpath=False):
        _dict = get_public_members(self)
        if use_relpath:
            _dict['file'] = relpath(_dict['file'])
        return _dict
