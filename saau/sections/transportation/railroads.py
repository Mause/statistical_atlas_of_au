from . import TransportationImageProvider
from ...utils.header import render_header_to


class RailroadImageProvider(TransportationImageProvider):
    path = 'railroad_paths.json'
    layers = ['Railways']

    def build_image(self):
        return render_header_to(
            self.services.fonts.get_font(),
            super().build_image(),
            19.5,
            [
                '<b>MAP OF</b>',
                '<b>RAILROADS IN AUSTRALIA</b>',
                '<i>Compiled using data from Geography Australia</i>'
            ]
        )
