import pickle
from collections import namedtuple

import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.io.shapereader as shpreader


name = lambda q: q.attributes['NAME_1']
LL = namedtuple('LL', 'lat,lon')

AUS_NW = LL(111.5, -7)
AUS_SE = LL(155, -42)


def get(key, records):
    for record in records:
        if name(record) == key:
            return record


def get_states():
    try:
        with open('geometries.pickle', 'rb') as fh:
            val = pickle.load(fh)

    except FileNotFoundError:
        shpfile = shpreader.Reader("AUS_adm\\AUS_adm1")
        val = list(zip(shpfile.records(), shpfile.geometries()))

        with open('geometries.pickle', 'wb') as fh:
            pickle.dump(val, fh)

    return val


def get_map():
    # [0, 0, 1, 1]
    ax = plt.axes([0, 0, 1, 1], projection=ccrs.Mercator())

    show_world = False
    if show_world:
        ax.set_global()
    else:
        extents = [AUS_NW.lat, AUS_SE.lat, AUS_NW.lon, AUS_SE.lon]
        ax.set_extent(extents, ccrs.Geodetic())

    # to get the effect of having just the states without a map "background"
    # turn off the outline and background patches
    # ax.background_patch.set_visible(False)
    # ax.outline_patch.set_visible(False)

    ax.add_geometries(
        [
            state
            for record, state in get_states()
            if 'island' not in name(record).lower()
        ],
        ccrs.PlateCarree(),
        facecolor='LightGrey', edgecolor='black',
        zorder=0
    )

    return ax
