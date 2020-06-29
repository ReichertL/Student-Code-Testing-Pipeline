"""
Create ASCII and HTML tables using only python format strings.

"""
import re
from string import Formatter

FORMATTER = Formatter()


def fmt_parse(*args):
    """Prase {} tyep format string. Used to extract format specs."""
    return FORMATTER.parse(*args)


CSS_HIGHLIGHT = "color: green;"

_RE_FORMAT_SPEC = re.compile(r'(?:(?P<fill>.)?(?P<align>[<>=^]))?'
                             r'(?P<sign>[-+ ])?'
                             r'(?P<alternate>#)?'
                             r'(?P<zero>0)?'
                             r'(?P<width>\d+)?'
                             r'(?P<comma>,)?'
                             r'(?:\.(?P<precision>\d+))?'
                             r'(?P<test_case_type>[a-zA-Z%])?')


def _parse_format_spec(format_spec):
    """
Parse the string format_spec and return a dict with the following entries:

  fill             fill character for padding
  align            alignment in '<^>='
  sign             sign in '+- '
  alternate        alternate form specified
  zero             whether to pad with zeros
  width : int      minimum width
  comma            use comma as thousands seperator
  precision : int  number of digits after decimal point
  test_case_type             character describing conversion test_case_type

Default values for test_case_type and alignment are set appropriately.

Examples:

>>> next(fmt_parse('abc{num!a:>d}'))
('abc', 'num', '>d', 'a')

>>> _parse_format_spec('d')
{'fill': '', 'align': '>', 'sign': None, 'alternate': None, 'zero': None,\
 'width': None, 'comma': None, 'precision': None, 'test_case_type': 'd'}

>>> _parse_format_spec('=^-#06,.3f')
{'fill': '=', 'align': '^', 'sign': '-', 'alternate': '#', 'zero': '0',\
 'width': '6', 'comma': ',', 'precision': '3', 'test_case_type': 'f'}

"""

    match_object = _RE_FORMAT_SPEC.match(format_spec)
    if match_object is None:
        raise ValueError()
    res = match_object.groupdict()
    if res['test_case_type'] is None:  # the default test_case_type is 's'
        res['test_case_type'] = 's'
    if res['fill'] is None:
        res['fill'] = ''
    if res['align'] is None:  # assign the default alignment
        if res['test_case_type'] in 'bcdoxXneEfFgGn%':
            res['align'] = '>'
        else:
            res['align'] = '<'
    return res


def _pad(s: str, width: int, alignment: str, fill):
    """Pad the string s to the given width, using alignemnt and fill.
>>> _pad('abc', 5, '>', '')
'  abc'
>>> _pad('abc', 5, '<', '')
'abc  '
>>> _pad('abc', 5, '^', '#')
'#abc#'
>>> _pad('ab', 1, '>', '')
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
ValueError: "ab" is longer than 1
    """
    if width < len(s):
        raise ValueError('"{}" is longer than {:d}'.format(s, width))
    return format(s, fill + alignment + str(width))


def _format_is_float(fspec):
    """Return if test_case_type is 'f' and precision unequal to zero.

>>> _format_is_float({'test_case_type': 'f', 'precision': None})
True
>>> _format_is_float({'test_case_type': 'f', 'precision': '0'})
False
>>> _format_is_float({'test_case_type': 'f', 'precision': '1'})
True
    """
    prec = fspec['precision']
    return fspec['test_case_type'] == 'f' and (prec is None or int(prec) > 0)


def list_from_dict(keys, dictionary):
    """
>>> list_from_dict([1,3,2], {1: 'a', 2: 'b', 3: 'c'})
['a', 'c', 'b']
    """
    if isinstance(dictionary, dict):
        return [dictionary[k] for k in keys if k]
    return list(dictionary)


def format_or_empty(value, fmt, spec):
    """Format `value` according to `fmt`. Return `''` if `value` is `None`.

    If spec['test_case_type'] is 's' (string), just return value.
    """
    if value is None:
        return ''
    if spec['test_case_type'] in 's':
        return value
    return format(value, fmt)


def table_format(row_fmt, rows, titles=None, html=False, highlight=None):
    """
Create an ASCII (or HTML) table using python format string syntax.

Given one format string fmt and a sequence of value dicts rows = [d0, d1, ...],
such that fmt.format(**d0), fmt.format(**d1), ... produce the desired
output. `tableformat(fmt, rows, ...)` will return an ASCII table with constant
width columns.

Additional features:
    - `rows` may be a list of lists as well (positional format strings)
    - a titles row may be added
    - html output can be generated

Examples:
>>> fmt = '| {num:3d} | {string:>5s} |'
>>> val = [{'num': 23, 'string': 'abcdef'}, \
           {'num': 123456, 'string': 'ghi'}]
>>> print(fmt.format(**val[0]))
|  23 | abcdef |

>>> print(fmt.format(**val[1]))
| 123456 |   ghi |

>>> print(table_format(fmt, val))
|     23 | abcdef |
| 123456 |    ghi |
<BLANKLINE>

>>> print(table_format(fmt, val, titles='auto'))
|    num | string |
-------------------
|     23 | abcdef |
| 123456 |    ghi |
<BLANKLINE>

>>> print(table_format(fmt, val, titles=['first', 'second']))
|  first | second |
-------------------
|     23 | abcdef |
| 123456 |    ghi |
<BLANKLINE>

Using pure positional format strings:
>>> fmt_list = '| {:3d} | {:>5s} |'
>>> val_list = [[23, 'abcdef'], [123456, 'ghi']]
>>> print(table_format(fmt_list, val_list))
|     23 | abcdef |
| 123456 |    ghi |
<BLANKLINE>

    """
    if not row_fmt.endswith('\n'):
        row_fmt += '\n'
    formats = tuple(fmt_parse(row_fmt))
    if titles == 'auto':
        titles = [fmt[1] for fmt in formats if fmt[1] is not None]
    fspecs = [_parse_format_spec(fmt[2])
              for fmt in formats if fmt[2] is not None]
    # make lists from dicts, if needed
    rows = [list_from_dict((fmt[1] for fmt in formats), row) for row in rows]
    # format each value in each row:
    frows = [[format_or_empty(value, fmt[2], spec)
              for value, fmt, spec in zip(row, formats, fspecs)]
             for row in rows]

    # compute column widths
    lengths = [max(len(frow[i]) for frow in frows) for i in range(len(fspecs))]
    if titles is not None:
        assert len(titles) == len(fspecs)
        lengths = list(map(max, zip(lengths, map(len, titles))))
    reslist = []
    if not html:
        if titles is not None:
            titles += (len(formats) - len(titles)) * ['']
            for s, length, fmt, fspec in zip(
                    titles, lengths, formats, fspecs):
                reslist.append(fmt[0])
                reslist.append(_pad(s, length, fspec['align'], fspec['fill']))
            reslist.append(formats[-1][0])
            reslist.append((sum(map(len, reslist)) - 1) * '-' + '\n')
        for frow in frows:
            for s, length, fmt, fspec in zip(frow, lengths, formats, fspecs):
                reslist.append(fmt[0])
                reslist.append(_pad(s, length, fspec['align'], fspec['fill']))
            reslist.append(formats[-1][0])
        return ''.join(reslist)
    # this html mode is a pile of crap
    table = HtmlTable(fspecs, highlight=highlight)
    table.add_titles(titles)
    for row in rows:
        table.start_row()
        for value, fmt, fspec in zip(row, formats, fspecs):
            table.add_cell(value, fmt, fspec)
        table.end_row()
    return table.shipout()


def css_align(fspec) -> str:
    """CSS equivalent of `fspec['align']`.

    WARNING: Implementation incomplete.
    """
    if fspec['align'] == '>':
        return 'text-align:right; '
    return ''


class HtmlTable:
    """Ugly html table formatter.

    Inline CSS is required, because we want to be able to paste it into
    moodle.
    """

    def __init__(self, format_specs, highlight=None):
        self.format_specs = format_specs
        self.highlight = highlight
        self.float_columns = [_format_is_float(fs) for fs in format_specs]
        self.parts = ['<table style="border-collapse: collapse;">\n']
        self.num_rows = 0
        self.column = None

    def _add(self, *args):
        """Extend `self.parts` by `args`."""
        self.parts += args

    def add_titles(self, titles) -> None:
        """Add a title row."""
        if titles is None:
            return
        self._add('  <tr style="border-bottom-width: 1px;'
                  ' border-bottom-style: solid;">\n')
        for title, isfloat in zip(titles, self.float_columns):
            self._add('<th')
            if isfloat:
                self._add(' colspan="2"')
            self._add(' style="padding-left:6pt;padding-right:6pt;">')
            self._add(title)
            self._add('</th>')
        self._add('\n  </tr>\n')
        self.num_rows += 1

    def start_row(self):
        """Begin table row."""
        assert self.column is None
        self.column = 0
        if self.num_rows % 2 == 0:
            self._add('  <tr>')
        else:
            self._add('  <tr style="background-color: #dddddd;">')

    def end_row(self):
        """End table row."""
        assert self.column is not None
        self.column = None
        self._add('</tr>\n')
        self.num_rows += 1

    def add_cell(self, value, fmt, fspec):
        """Insert <td> element."""
        fm_td = '<td style="{}{}{}">{}</td>'
        fm_td_float = (
            '<td align="right" style="{}padding-right: 0px">{}.</td>'
            '<td align="left" style="padding-left: 0px; {}";>{}</td>')
        lborder = ('padding-left:6pt; '
                   'border-left-width: 1px; '
                   'border-left-style: solid;') if self.column else ''
        rborder = " padding-right:6pt;"
        fvalue = format(value, fmt[2])
        if self.highlight is not None and fmt[1] == self.highlight:
            lborder += CSS_HIGHLIGHT
            rborder += CSS_HIGHLIGHT
        if _format_is_float(fspec):
            left, right = fvalue.split('.')
            self._add(fm_td_float.format(lborder, left, rborder, right))
        else:
            self._add(fm_td.format(lborder, rborder, css_align(fspec), fvalue))
        self.column += 1

    def shipout(self):
        """Return the whole table as `str`."""
        return ''.join(self.parts + ['</table\n'])


def html_table_demo():
    """Example html table for testing purposes."""
    with open('foo.html', 'w') as file:
        file.write(table_format(
            '| {:f} | {:d} | {}',
            [[.123, 123, 'a'],
             [123.456, 4560, 'aoiansdofaiefansdf'],
             [4623.456, 100, 'aoifansdf'],
             ],
            titles=['float', 'int', 'str'],
            html=True))


if __name__ == '__main__':
    html_table_demo()
