import os
import json
from os.path import join, exists

import cartopy.crs as ccrs
import shapely.geometry as sgeom
import matplotlib.pyplot as plt

from ..aus_map import get_map
from .data import get_paths


def build_from_paths(paths):
    aus_map = get_map()

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

from ..image_provider import ImageProvider


class TransportationImageProvider(ImageProvider):
    def __init__(self, data_dir):
        super().__init__(data_dir)

        assert hasattr(self, 'path')
        assert hasattr(self, 'layers')

    def obtain_data(self):
        data = get_paths(self.layers).tolist()
        with open(join(self.data_dir, self.path), 'w') as fh:
            json.dump(data, fh)

    def has_required_data(self):
        if not self.data_dir_exists(self.path):
            return False

        # some extra validation
        filename = join(self.data_dir, self.path)
        try:
            with open(filename) as fh:
                return bool(json.load(fh))
        except ValueError:
            os.unlink(filename)
            return False

    def build_image(self, output_filename):
        with open(join(self.data_dir, self.path)) as fh:
            paths = json.load(fh)

        build_from_paths(paths)
        plt.savefig(output_filename)

# 'ferrys',
IMAGES = [
    'railroads.RailroadImageProvider',
    'roads.RoadImageProvider'
]
