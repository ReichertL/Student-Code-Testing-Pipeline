class ColoredString(object):
    def __init__(self, s, length):
        self.s = s
        self.length = length

    def __str__(self):
        return self.s

    def __len__(self):
        return self.length

    def __format__(self, format_spec):
        align = '<'
        if format_spec and format_spec[0] in '<>^':
            align = format_spec[0]
            format_spec = format_spec[1:]
        if format_spec[-1:] == 's':
            format_spec = format_spec[:-1]
        s = str(self)
        width = 0 if format_spec == '' else int(format_spec)
        spaces = max(0, width - len(self))
        if align == '<':
            return s + spaces * ' '
        if align == '>':
            return spaces * ' ' + s
        if align == '^':
            return (spaces // 2) * ' ' + s + (spaces - spaces // 2) * ' '

    def __add__(self, other):
        if isinstance(other, ColoredString):
            return ColoredString(self.s + other.s, self.length + other.length)
        else:
            return ColoredString(self.s + other, self.length + len(other))

    def __radd__(self, other):
        if isinstance(other, ColoredString):
            return ColoredString(other.s + self.s, self.length + other.length)
        else:
            return ColoredString(other + self.s, self.length + len(other))
