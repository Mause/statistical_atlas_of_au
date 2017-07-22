# ancestry-russian
from . import AncestryImageProvider
from ...utils.header import render_header_to


class RussianAncestryImageProvider(AncestryImageProvider):
    filename = 'russian.json'
    ancestry_name = 'Russian'

    def build_image(self):
        return render_header_to(
            self.services.fonts.get_font(),
            super().build_image(),
            19,
            lines=[
                '<b>MAP</b>',
                'SHOWING THE DISTRIBUTION OF',
                '<b>RUSSIAN ANCESTRY</b>',

                # !!!!
                'ACCORDING TO THEIR PROPORTION TO THE AGGREGATE POPULATION',

                '<i>Compiled using data from the 2011 ABS Census</i>'
            ]
        )
