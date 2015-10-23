# geology-elevation1
from os.path import basename

import cartopy.crs as ccrs

from ..image_provider import ImageProvider
from ...utils.download import get_binary
from ...utils.shape import shape_from_zip

URL = 'http://www.ga.gov.au/corporate_data/48006/48006_shp.zip'
FILENAME = basename(URL)


class ElevationImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        return get_binary(URL, self.data_dir_join(FILENAME))

    def build_image(self):
        shp = shape_from_zip(self.data_dir_join(FILENAME))

        aus_map = self.services.aus_map.get_map()

        aus_map.add_geometries(
            [rec.geometry for rec in shp.records()],
            crs=ccrs.PlateCarree()
        )

        return aus_map
