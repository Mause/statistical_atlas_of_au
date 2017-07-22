from . import TransportationImageProvider
from ...utils.header import render_header_to


class RoadImageProvider(TransportationImageProvider):
    path = 'road_paths.json'
    layers = ['All_Roads', 'Major_Road_Network']

    def build_image(self):
        return render_header_to(
            self.services.fonts.get_font(),
            super().build_image(),
            19.5,
            [
                '<b>MAP OF</b>',
                '<b>MAJOR ROADS IN AUSTRALIA</b>',
                '<i>Compiled using data from Geography Australia</i>'
            ]
        )
