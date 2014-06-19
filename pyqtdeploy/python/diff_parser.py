# Copyright (c) 2014, Riverbank Computing Limited
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.


from ..user_exception import UserException


class _DiffException(UserException):
    """ A UserException specifically related to an unexpected diff file format.
    """

    def __init__(self, line_nr, detail):
        """ Initialise the object. """

        super().__init__("Unexpected diff format",
                "{0}:{1}".format(line_nr + 1, detail))


class _FileDiff:
    """ Encapsulate the diff for a single file. """

    def __init__(self):
        """ Initialise the object. """

        self.file_name = ''
        self.hunks = []


class _Hunk:
    """ Encapsulate a hunk. """

    def __init__(self, old_range, new_range):
        """ Initialise the object.  old_range is a 2-tuple of the line number
        and number of lines in the section to be removed.  new_range is a
        2-tuple of the line number and number of lines in the section to be
        added.
        """

        self.old_range = old_range
        self.new_range = new_range
        self.lines = []


def parse_diffs(diff):
    """ Parse a diff and return a list of _FileDiff instances. """

    WANT_DIFF, WANT_OLD, WANT_NEW, WANT_RANGES, WANT_BODY = range(5)

    want = WANT_DIFF

    diffs = []

    for line_nr, line in enumerate(diff.split('\n')):
        words = line.data().decode('latin1').split()

        if want == WANT_DIFF:
            if len(words) == 0 or words[0] != 'diff':
                raise _DiffException(line_nr, "diff command line expected")

            diffs.append(_FileDiff())

            want = WANT_OLD
        elif want == WANT_OLD:
            if len(words) < 3 or words[0] != '---':
                raise _DiffException(line_nr, "--- line expected")

            # Remove the root directory from the name of the file being
            # patched.  We assume we won't have a diff with paths containing
            # spaces.
            _, file_name = words[1].split('/', maxsplit=1)
            diffs[-1].file_name = file_name

            want = WANT_NEW
        elif want == WANT_NEW:
            if len(words) < 3 or words[0] != '+++':
                raise _DiffException(line_nr, "+++ line expected")

            want = WANT_RANGES
        elif want == WANT_RANGES:
            _parse_hunk_header(diffs, words, line_nr)

            want = WANT_BODY
        elif want == WANT_BODY:
            if len(words) != 0:
                if words[0] == 'diff':
                    diffs.append(_FileDiff())
                    want = WANT_OLD
                    continue

                if words[0] == '@@':
                    _parse_hunk_header(diffs, words, line_nr)
                    continue

            diffs[-1].hunks[-1].lines.append(line)

    if want != WANT_BODY:
        raise _DiffException(line_nr, "diff seems to be truncated")

    return diffs


def _parse_hunk_header(diffs, words, line_nr):
    """ Parse a hunk header line and add it to the current diff. """

    if len(words) != 4 or words[0] != '@@' or words[3] != '@@':
        raise _DiffException(line_nr, "hunk header line expected")

    old_range = _parse_range(words[1], '-')
    if old_range is None:
        raise _DiffException(line_nr, "invalid -range")

    new_range = _parse_range(words[2], '+')
    if new_range is None:
        raise _DiffException(line_nr, "invalid +range")

    diffs[-1].hunks.append(_Hunk(old_range, new_range))


def _parse_range(range_str, prefix):
    """ Parse a hunk range and return a 2-tuple of the line number and number
    of lines.  Return None if there was an error.
    """

    if range_str[0] != prefix:
        return None

    line_nr, nr_lines = range_str[1:].split(',', maxsplit=1)

    try:
        line_nr = int(line_nr)
    except ValueError:
        return None

    try:
        nr_lines = int(nr_lines)
    except ValueError:
        return None

    return (line_nr, nr_lines)
