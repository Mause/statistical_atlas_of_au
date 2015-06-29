import json
from itertools import tee, chain

from aus_map import get_map
from data import get_paths

from betamax import Betamax
import arcrest.compat
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
import numpy as np
import requests
import shapely.geometry as sgeom


import logging
from unittest.mock import patch
from collections import namedtuple
from contextlib import contextmanager
logging.basicConfig(level=logging.DEBUG)
Res = namedtuple('Res', 'url,headers,read')


@contextmanager
def compat():
    """
    Patches in heavy-duty caching and requests-lib use
    """
    def side_effect(req):
        r = requests.get(
            req.get_full_url(),
            req.headers,
            data=req.data
        )

        return Res(r.url, r.headers, lambda: r.content)

    arcrest.compat.sess = requests.Session()
    with patch('arcrest.compat.urllib2.urlopen', side_effect=side_effect):
        with Betamax(arcrest.compat.sess).use_cassette('cache'):
            yield


def get_cached_paths():
    try:
        with open('paths.json') as fh:
            val = np.array(json.load(fh))

    except FileNotFoundError:
        with compat():
            val = get_paths()

        with open('paths.json', 'w') as fh:
            json.dump(val.tolist(), fh)

    return val


def main():
    print('loading paths')
    transport_paths = get_cached_paths()
    print(len(transport_paths), 'paths load')

    print(sum(map(len, transport_paths)), 'waypoints within said paths')

    print('building map')
    aus_map = get_map()
    print('map built')

    LineString = sgeom.LineString
    paths = [
        LineString(tuple(map(tuple, waypoints)))
        for waypoints in transport_paths
    ]

    # import IPython
    # IPython.embed()

    print('paths sum', sum(path.length for path in paths), 'in length')

    print('tracing paths')
    aus_map.add_geometries(
        paths,
        ccrs.PlateCarree(),
        alpha=0.7,
        linewidth=1,
        zorder=2,
    )
    print('paths added to map')

    aus_map.set_aspect(1)

    print('rendering map')
    plt.savefig('map.png')
    print('map rendered')

if __name__ == '__main__':
    main()
