# ancestry-italian
from . import AncestryImageProvider
from ...utils.header import render_header_to


class ItalianAncestryImageProvider(AncestryImageProvider):
    filename = 'italian.json'
    ancestry_name = 'Italian'

    def build_image(self):
        return render_header_to(
            super().build_image(),
            19,
            lines=[
                '<b>MAP</b>',
                'SHOWING THE DISTRIBUTION OF',
                '<b>ITALIAN ANCESTRY</b>',

                # !!!!
                'ACCORDING TO THEIR PROPORTION TO THE AGGREGATE POPULATION',

                '<i>Compiled using data from the 2011 ABS Census</i>'
            ]
        )
