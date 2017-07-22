import numpy as np
from lxml.etree import fromstring, XMLSyntaxError


def parse_lines(lines):
    for line in lines:
        try:
            xml_line = fromstring(line.encode('utf-8'))
        except XMLSyntaxError:
            attrs = []
        else:
            line = list(xml_line.getiterator())
            attrs = [thing.tag for thing in line]
            line = line[-1].text

        yield line, attrs


def render_header_to(font, ax, sy, lines, sx=0.5):
    y_points = (
        q / 20
        for q in np.arange(sy, 0, -0.5)
    )

    for y, (text, attrs) in zip(y_points, parse_lines(lines)):
        line = ax.figure.text(sx, y, text, ha='center')

        if 'b' in attrs:
            line.set_weight('extra bold')
            line.set_font_properties(font)
            line.set_fontsize(25)
        if 'i' in attrs:
            line.set_style('italic')

    return ax
