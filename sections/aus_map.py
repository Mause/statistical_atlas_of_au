import logging
from collections import namedtuple
from os.path import dirname, join, exists
import pickle

import requests
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from .shape import shape_from_zip
from .image_provider import RequiresData

name = lambda q: q.attributes['NAME_1']
LL = namedtuple('LL', 'lat,lon')

AUS_NW = LL(111.5, -7)
AUS_SE = LL(155, -42)
YELLOWED_PAPER = '#F1E4BB'


def get(key, records):
    for record in records:
        if name(record) == key:
            return record


def get_states():
    data_dir = AusMap(None).data_dir

    geometries_cache = join(data_dir, 'geometries.pickle')

    try:
        with open(geometries_cache, 'rb') as fh:
            return pickle.load(fh)

    except FileNotFoundError:
        pass

    shpfile = shape_from_zip(
        join(data_dir, "AUS_adm.zip"),
        "AUS_adm1"
    )

    val = list(shpfile.records())

    with open(geometries_cache, 'wb') as fh:
        pickle.dump(val, fh)

    return val


def get_map(show_world=False):
    # [0, 0, 1, 1]
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.Mercator())

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
    ax.set_axis_bgcolor(YELLOWED_PAPER)

    logging.info('Adding states to map')
    ax.add_geometries(
        [
            record.geometry
            for record in get_states()
            if 'island' not in name(record).lower()
        ],
        ccrs.PlateCarree(),
        facecolor=YELLOWED_PAPER,
        edgecolor='black',
        zorder=0
    )
    logging.info('States added')

    return ax


class Singleton(type):
    def __call__(cls, *args, **kw):
        if hasattr(cls, '_instance'):
            return cls._instance

        cls._instance = cls.__new__(cls)
        cls._instance.__init__(*args, **kw)

        return cls._instance


class AusMap(RequiresData, metaclass=Singleton):
    def has_required_data(self):
        return self.data_dir_exists('AUS_adm.zip')

    def obtain_data(self):
        "http://www.gadm.org/download"
        r = requests.get(
            'http://biogeo.ucdavis.edu/data/gadm2/shp/AUS_adm.zip'
        )

        filename = join(self.data_dir, 'AUS_adm.zip')

        with open(filename, 'wb') as fh:
            fh.write(r.content)
