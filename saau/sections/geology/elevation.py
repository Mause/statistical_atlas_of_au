# geology-elevation1
from glob import glob
from os.path import basename, join

import rasterio
from cartopy.io import LocatedImage
from cartopy.io import srtm
import cartopy.crs as ccrs
import numpy as np
from rasterio.warp import reproject

from ..image_provider import ImageProvider
from ...utils.download import get_binary
from ...utils import unzip
from ...services.aus_map import AUS_NW, AUS_SE

URL = 'http://www.ga.gov.au/corporate_data/48006/48006_shp.zip'
FILENAME = basename(URL)


def load_data(self):
    dest = unzip(self.data_dir_join(FILENAME))
    path = join(dest, "globalmap2001/Raster/elevation")

    for filename in glob(join(path, '*.bil')):
        yield rasterio.open(filename)


def timer(func):
    def wrapper(*args, **kwargs):
        import time
        start = time.time()
        val = func(*args, **kwargs)
        print(func.__name__, time.time() - start)
        return val
    return wrapper


def fetch_raster(self):
    for bil in load_data(self):
        # read image into ndarray
        src = bil.read()

        dest = np.empty(shape=src.shape, dtype=np.uint8)
        timer(reproject)(
            src,
            dest,
            src_crs={'init': 'EPSG:4019'},
            src_transform=bil.affine,
            dst_crs={'init': 'EPSG:4326'},
            dst_transform=bil.affine
        )

        affine = bil.affine
        xmin = affine.c
        xmax = affine.c + (affine.a * bil.width)
        ymin = affine.f + (affine.e * bil.height)
        ymax = affine.f

        yield LocatedImage(
            np.array(dest[0]),
            (xmin, xmax, ymin, ymax)
        )


def shade(located_elevations):
    """
    Given an array of elevations in a LocatedImage, add a relief (shadows) to
    give a realistic 3d appearance.

    """
    new_img = srtm.add_shading(located_elevations.image,
                               azimuth=135, altitude=15)
    return LocatedImage(new_img, located_elevations.extent)


class ElevationImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        return get_binary(URL, self.data_dir_join(FILENAME))

    def build_image(self):
        images = fetch_raster(self)
        ax = self.services.aus_map.get_map(show_world=True)

        x = (AUS_NW[0], AUS_SE[0])
        y = (AUS_NW[1], AUS_SE[1])
        ax.set_extent(
            [
                min(x),
                max(x),
                min(y),
                max(y)
            ],
            ccrs.PlateCarree()
        )

        for img in images:
            timer(ax.imshow)(
                img.image,
                origin='upper',
                extent=img.extent,
                transform=ccrs.PlateCarree()
            )
        # ax.coastlines(resolution='50m', color='black', linewidth=1)
        # ax.gridlines()
        # 2014\05\09

        return ax
