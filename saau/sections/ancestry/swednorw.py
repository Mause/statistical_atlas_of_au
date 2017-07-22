# ancestry-swednorw
from . import AncestryImageProvider
from ...utils.header import render_header_to


class SwedishNorwegionAncestryImageProvider(AncestryImageProvider):
    filename = 'SwedishNorwegion.json'
    ancestry_name = 'SwedishNorwegion'

    def build_image(self):
        return render_header_to(
            self.services.fonts.get_font(),
            super().build_image(),
            19,
            lines=[
                '<b>MAP</b>',
                'SHOWING THE DISTRIBUTION OF',
                '<b>Swedish/Norwegion ANCESTRY</b>',

                # !!!!
                'ACCORDING TO THEIR PROPORTION TO THE AGGREGATE POPULATION',

                '<i>Compiled using data from the 2011 ABS Census</i>'
            ]
        )
