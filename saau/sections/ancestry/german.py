# ancestry-german
from . import AncestryImageProvider
from ...utils.header import render_header_to


class GermanAncestryImageProvider(AncestryImageProvider):
    filename = 'german.json'
    ancestry_name = 'German'

    def build_image(self):
        return render_header_to(
            super().build_image(),
            19,
            lines=[
                '<b>MAP</b>',
                'SHOWING THE DISTRIBUTION OF',
                '<b>GERMAN ANCESTRY</b>',

                # !!!!
                'ACCORDING TO THEIR PROPORTION TO THE AGGREGATE POPULATION',

                '<i>Compiled using data from the 2011 ABS Census</i>'
            ]
        )
