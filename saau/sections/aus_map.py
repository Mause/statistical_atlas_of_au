import logging
from collections import namedtuple
from shutil import copyfileobj
import pickle

import requests
import matplotlib.pyplot as plt
import cartopy.crs as ccrs

from . import Singleton
from .shape import shape_from_zip
from .image_provider import RequiresData

name = lambda q: q.attributes['NAME_1']
DummyRecord = namedtuple('DummyRecord', 'attributes,geometry')
LL = namedtuple('LL', 'lat,lon')

AUS_NW = LL(111.5, -1)
AUS_SE = LL(155, -42)
YELLOWED_PAPER = '#F1E4BB'


def get(key, records):
    for record in records:
        if name(record) == key:
            return record


def get_states():
    aus_map_inst = AusMap(None)
    geometries_cache = aus_map_inst.data_dir_join('geometries.pickle')

    try:
        with open(geometries_cache, 'rb') as fh:
            return pickle.load(fh)

    except (FileNotFoundError, EOFError):
        pass

    shpfile = shape_from_zip(
        aus_map_inst.data_dir_join("AUS_adm.zip"),
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
        # facecolor='LightGrey',
        facecolor=YELLOWED_PAPER,
        edgecolor='black',
        zorder=zorder
    )
    logging.info('States added')

    return ax


class AusMap(RequiresData, metaclass=Singleton):
    def has_required_data(self):
        return self.data_dir_exists('AUS_adm.zip')

    def obtain_data(self):
        "http://www.gadm.org/download"
        r = requests.get(
            'http://biogeo.ucdavis.edu/data/gadm2/shp/AUS_adm.zip',
            stream=True
        )

        with open(self.data_dir_join('AUS_adm.zip'), 'wb') as fh:
            copyfileobj(r.raw, fh)

        return True
