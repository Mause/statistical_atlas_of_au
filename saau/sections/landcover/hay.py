import logging

import cartopy.crs as ccrs

from .data import LandcoverImageProvider, load_data
from ...utils.header import render_header_to

ALUM = {'3.3.3 Hay & silage', '3.3.3'}


def key(record):
    return (
        record.get('LU_CODE_1') in ALUM or
        record.get('TERTIARY_V') in ALUM
    )


class HayImageProvider(LandcoverImageProvider):

    def build_image(self):
        data = load_data(self.data_dir)

        data = filter(key, data)
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

        return render_header_to(
            self.services.fonts.get_font(),
            aus_map,
            19.5,
            [
                '<b>MAP</b>',
                'SHOWING THE RANGE OF LAND COVER FOR',
                '<b>HAY</b>',
                'WITHIN THE TERRITORY OF AUSTRALIA',
                '<i>Compiled using data from the Department of Agriculture</i>'
            ]
        )
