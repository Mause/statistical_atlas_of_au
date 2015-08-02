import json
import logging
from os.path import join

import pandas
import numpy as np
import matplotlib as mpl
import cartopy.crs as ccrs
from matplotlib.cm import get_cmap

from ..abs import get_generic_data, collapse_concepts
from ..image_provider import ImageProvider

filename = 'ABS_ANNUAL_ERP_LGA2014.json'


def get_data(data_dir):
    with open(join(data_dir, filename)) as fh:
        data = json.load(fh)

    data = [
        dict(
            collapse_concepts(locale['concepts']),
            **observation
        )
        for locale in data['series']
        for observation in locale['observations']
    ]

    df = pandas.DataFrame(data).convert_objects(convert_numeric=True)

    return df[df.Time == 2014]


clean_region = lambda region: ' '.join(region.split()[:-1])


def is_locatable(towns):
    return lambda row: clean_region(row.Region) in towns


get_town = None


def main(services, data_dir, output_filename):
    logging.info('loading data')
    dat = get_data(data_dir)

    logging.info('finding towns')

    valid = [
        row.Region
        for idx, row in dat.iterrows()
        if get_town(towns, row.Region)
    ]

    norm = mpl.colors.Normalize(
        vmin=dat.Value.min(),
        vmax=dat.Value.max()
    )
    cmap = get_cmap('hot')
    populations = np.array([
        (
            row.Region, row.Value,
            get_town(towns, row.Region),
            cmap(norm(row.Value))
        )
        for _, row in dat[dat.Region.isin(valid)].iterrows()
    ])

    logging.info('building map')

    aus_map = services.aus_map.get_map()

    logging.info('mapping %d towns', len(populations))
    for name, population, rec, color in populations:
        aus_map.add_geometries(
            [rec.geometry],
            crs=ccrs.PlateCarree(),
            facecolor=color,
            edgecolor='grey'
        )

    cax = aus_map.figure.add_axes([0.95, 0.2, 0.02, 0.6])
    cb = mpl.colorbar.ColorbarBase(
        cax,
        cmap=cmap,
        norm=norm,
        spacing='props'
    )
    cb.set_label('Population')

    return aus_map


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

    def build_image(self, output_filename):
        __import__('ipdb').set_trace()
        return main(self.services, self.data_dir, output_filename)
