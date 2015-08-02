from . import TransportationImageProvider
from ..misc.header import render_header_to


class RailroadImageProvider(TransportationImageProvider):
    path = 'railroad_paths.json'
    layers = ['Railways']

    def build_image(self, _):
        return render_header_to(
            super().build_image(_),
            19.5,
            [
                '<b>MAP OF</b>',
                '<b>RAILROADS IN AUSTRALIA</b>',
                '<i>Compiled using data from Geography Australia</i>'
            ]
        )
