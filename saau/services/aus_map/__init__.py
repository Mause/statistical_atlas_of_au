import logging
from collections import namedtuple
import pickle
from os.path import basename

import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from ...utils.shape import shape_from_zip
from ...sections.image_provider import RequiresData
from ...utils.download import get_binary

name = lambda q: q.attributes['NAME_1']
DummyRecord = namedtuple('DummyRecord', 'attributes,geometry')
LL = namedtuple('LL', 'lat,lon')

AUS_NW = LL(111.5, -1)
AUS_SE = LL(155, -42)
YELLOWED_PAPER = '#F1E4BB'

"http://www.gadm.org/download"
URL = 'http://biogeo.ucdavis.edu/data/gadm2.8/shp/AUS_adm_shp.zip'
FILENAME = basename(URL)


def get_states(services):
    geometries_cache = services.aus_map.data_dir_join('geometries.pickle')

    try:
        with open(geometries_cache, 'rb') as fh:
            return pickle.load(fh)

    except (FileNotFoundError, EOFError):
        pass

    shpfile = shape_from_zip(
        services.aus_map.data_dir_join(FILENAME),
        "AUS_adm1"
    )

    val = list(shpfile.records())

    val = [
        DummyRecord(
            rec.attributes,
            rec.geometry.simplify(0.5)
        )
        for rec in val
    ]

    with open(geometries_cache, 'wb') as fh:
        pickle.dump(val, fh)

    return val


def get_map(services, show_world=False, zorder=0):
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.Mercator())

    change = lambda x: (x / 100) * 2

    width, height = change(960), change(730)
    ax.figure.set_size_inches(width, height, forward=True)

    if show_world:
        ax.set_global()
    else:
        extents = [AUS_NW.lat, AUS_SE.lat, AUS_NW.lon, AUS_SE.lon]
        ax.set_extent(extents, ccrs.Geodetic())

    # to get the effect of having just the states without a map "background"
    # turn off the outline and background patches
    # ax.background_patch.set_visible(False)
    # ax.outline_patch.set_visible(False)

    ax.background_patch.set_facecolor(YELLOWED_PAPER)
    ax.patch.set_facecolor(YELLOWED_PAPER)
    ax.set_facecolor(YELLOWED_PAPER)

    logging.info('Adding states to map')
    ax.add_geometries(
        [
            record.geometry
            for record in get_states(services)
            if 'island' not in name(record).lower()
        ],
        ccrs.PlateCarree(),
        # facecolor='LightGrey',
        facecolor=YELLOWED_PAPER,
        edgecolor='black',
        zorder=zorder
    )
    logging.info('States added')

    return ax


class AusMap(RequiresData):

    def get_map(self, **kwargs):
        return get_map(self.services, **kwargs)

    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        return get_binary(
            URL,
            self.data_dir_join(FILENAME)
        )


SERVICES = ['__init__.AusMap']
