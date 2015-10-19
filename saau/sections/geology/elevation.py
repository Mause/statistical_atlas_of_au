# geology-elevation1
from os.path import basename

import cartopy.crs as ccrs

from ..image_provider import ImageProvider
from ...utils.download import get_binary
from ...utils.shape import shape_from_zip

url = 'http://www.ga.gov.au/corporate_data/48006/48006_shp.zip'
filename = basename(url)


class ElevationImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(filename)

    def obtain_data(self):
        return get_binary(url, self.data_dir_join(filename))

    def build_image(self):
        shp = shape_from_zip(self.data_dir_join(filename))

        aus_map = self.services.aus_map.get_map()

        aus_map.add_geometries(
            [rec.geometry for rec in shp.records()],
            crs=ccrs.PlateCarree()
        )

        return aus_map
