import os
import json

import cartopy.crs as ccrs
import shapely.geometry as sgeom

from ..image_provider import ImageProvider
from .data import get_paths


def build_from_paths(services, paths):
    aus_map = services.aus_map.get_map()

    LineString = sgeom.LineString
    paths = [
        LineString(tuple(map(tuple, waypoints)))
        for waypoints in paths
    ]

    aus_map.add_geometries(
        paths,
        ccrs.PlateCarree(),
        alpha=0.7,
        linewidth=1,
        zorder=2,
        # color='transparent'
    )

    aus_map.set_aspect(1)

    return aus_map


class TransportationImageProvider(ImageProvider):
    def __init__(self, data_dir, services):
        super().__init__(data_dir, services)

        assert hasattr(self, 'path')

    def obtain_data(self):
        assert hasattr(self, 'layers')
        return self.save_json(
            self.path,
            get_paths(self.layers).tolist()
        )

    def has_required_data(self):
        if not self.data_dir_exists(self.path):
            return False

        # some extra validation
        filename = self.data_dir_join(self.path)
        try:
            # ensure there's actually something in the file
            with open(filename) as fh:
                return bool(json.load(fh))
        except ValueError:
            # if the file doesn't contain valid json, remove it
            os.unlink(filename)
            return False

    def build_image(self, output_filename):
        return build_from_paths(
            self.services,
            self.load_json(self.path)
        )


IMAGES = [
    'ferrys.FerryImageProvider',
    'railroads.RailroadImageProvider',
    'roads.RoadImageProvider'
]
