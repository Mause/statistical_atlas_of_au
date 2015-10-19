import json
import logging
from os.path import join

import matplotlib as mpl
import cartopy.crs as ccrs
from matplotlib.cm import get_cmap

from ...utils.download.abs import get_generic_data, abs_data_to_dataframe
from ..image_provider import ImageProvider
from ...utils.header import render_header_to

filename = 'ABS_ANNUAL_ERP_LGA2014.json'


def get_data(data_dir):
    with open(join(data_dir, filename)) as fh:
        return abs_data_to_dataframe(json.load(fh))


def main(services, data_dir):
    logging.info('loading data')
    dat = get_data(data_dir)

    norm = mpl.colors.Normalize(
        vmin=dat.Value.min(),
        vmax=546067  # has an outlier
    )
    cmap = get_cmap('hot_r')

    logging.info('building map')

    aus_map = services.aus_map.get_map()

    logging.info('Adding data')
    for _, row in dat.iterrows():
        recs = services.lga.get('LGA_CODE11', row.LGA2014)

        aus_map.add_geometries(
            [rec.geometry for rec in recs.rec],
            crs=ccrs.PlateCarree(),
            facecolor=cmap(norm(row.Value)),
            edgecolor='grey'
        )

    left, bottom, width, height = 0.90, 0.2, 0.02, 0.6
    cax = aus_map.figure.add_axes([left, bottom, width, height])
    cb = mpl.colorbar.ColorbarBase(
        cax,
        cmap=cmap,
        norm=norm,
        spacing='props'
    )
    cb.set_label('Population')

    return render_header_to(
        aus_map,
        19.5,
        [
            '<b>MAP</b>',
            'SHOWING THE FIVE DEGREES OF DENSITY, THE DISTRIBUTION',
            '<b>OF</b>',
            'POPULATION',
            '<i>'
            'Compiled using estimates from the Australian Bureau of Statistics'
            '</i>'
        ]
    )


class PopulationDensityImageProvider(ImageProvider):

    def has_required_data(self):
        if not self.data_dir_exists(filename):
            return False

        with open(self.data_dir_join(filename)) as fh:
            return bool(fh.read())

    def obtain_data(self):
        data = get_generic_data(
            'ABS_ANNUAL_ERP_LGA2014',
            and_=[
                'FREQUENCY.A',
                'REGIONTYPE.LGA2014',
                'MEASURE.ERP',
            ]
        )
        return self.save_json(filename, data)

    def build_image(self):
        return main(self.services, self.data_dir)
