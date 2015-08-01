import logging

import cartopy.crs as ccrs

from .data import LandcoverImageProvider, load_data

ALUM = ['3.3.3 Hay & silage']


class HayImageProvider(LandcoverImageProvider):
    def build_image(self, output_filename):
        data = load_data(self.data_dir)

        data = filter(
            lambda record: record['TERTIARY_V'] in ALUM,
            data
        )

        data = list(data)
        logging.info('%d data thingies for hay', len(data))

        logging.info('Building geometries')
        geoms = [
            record['geom']()
            for record in data
        ]
        logging.info('Geometries built')

        aus_map = self.services.aus_map.get_map()

        logging.info('Adding hay data')
        aus_map.add_geometries(
            geoms,
            ccrs.PlateCarree(),
            alpha=0.7,
            linewidth=1,
            zorder=2,
            facecolor='#ECA55D',
            edgecolor='#ECA55D'
            # edgecolor='#00FFFF'
            # color='transparent'
        )

        return aus_map
