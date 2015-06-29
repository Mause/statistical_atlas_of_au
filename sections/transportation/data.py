from operator import attrgetter, itemgetter
from itertools import chain, tee

import sys
sys.path.insert(0, 'C:\\Users\\Dominic\\Dropbox\\temp\\arcrest')

from arcrest import Catalog
import numpy as np


def get_layers(service):
    return dict(zip(service.layernames, service.layers))


LAYERS = [
    'All_Roads',
    'Major_Road_Network',
    'National_Route_Number_Labels',
    'Railway_Bridges',
    'Railway_Crossing_Lines',
    'Railway_Stations',
    'Railways',
    'Road_Bridges_and_Fords',
    'Road_Crossing_Lines',
    'Roads_Scale_600000_to_300000',
    'Roads_Scale_7Million_to_600000',
    'State_Route_Number_Labels',
]


def mend(env):
    env.wkid = env.spatialReference.wkid
    return env


def get_data():
    catalog = Catalog('http://www.ga.gov.au/gis/rest/services/')
    topography = catalog['topography']
    service = topography['Dynamic_National_Map_Transport']
    layers = get_layers(service)

    return chain.from_iterable(
        layer.QueryLayer(Geometry=mend(layer.extent))
        for layer in (layers[layer] for layer in LAYERS)
    )


def pairs(iterator):
    first, second = tee(iterator)
    ret = zip(chain([None], second), first)
    next(ret)  # kill the first half-empty pair
    return ret


def get_paths():
    paths = get_data()
    paths = map(itemgetter('geometry'), paths)
    paths = filter(lambda path: hasattr(path, 'paths'), paths)
    paths = map(attrgetter('paths'), paths)
    paths = chain.from_iterable(paths)

    return np.array([
        tuple(
            (part.x, part.y)
            for part in path
        )
        for path in paths
    ])
