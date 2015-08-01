import matplotlib.pyplot as plt
from operator import gt, lt, itemgetter
from lxml.etree import fromstring, XMLSyntaxError


def frange(start, stop, step):
    cur = start
    op = gt if start > stop else lt

    while op(cur, stop):
        yield cur
        cur += step


def parse_lines(lines):
    for line in lines:
        try:
            xml_line = fromstring(line.encode('utf-8'))
        except XMLSyntaxError:
            attrs = []
        else:
            attrs = [thing.tag for thing in xml_line.getiterator()]
            line = list(xml_line.getiterator())[-1].text

        yield line, attrs


def render_header_to(ax, sy, lines, sx=0.5):
    calc = lambda q: q / 20
    y_points = map(calc, frange(sy, 0, -1))

    parsed = list(parse_lines(lines))
    lines = map(itemgetter(0), parsed)
    line_attrs = map(itemgetter(1), parsed)

    lines = [
        ax.figure.text(sx, y, text, ha='center')
        for y, text in zip(y_points, lines)
    ]

    for idx, attrs in enumerate(line_attrs):
        if 'b' in attrs:
            lines[idx].set_weight('extra bold')
        if 'i' in attrs:
            lines[idx].set_style('italic')

    return ax


class Header:
    __init__ = lambda self, _: None
    has_required_data = lambda _: True

    def build_image(self, _):
        ax = plt.axes()
        render_header_to(ax)
        plt.show()
        return ax