from operator import attrgetter, itemgetter
from itertools import chain, tee

import sys
sys.path.insert(0, 'C:\\Users\\Dominic\\Dropbox\\temp\\arcrest')

from arcrest import Catalog
import numpy as np


def get_layers(service):
    return dict(zip(service.layernames, service.layers))


def mend(env):
    env.wkid = env.spatialReference.wkid
    return env


def get_data(requested_layers):
    catalog = Catalog('http://www.ga.gov.au/gis/rest/services/')
    topography = catalog['topography']
    service = topography['Dynamic_National_Map_Transport']
    layers = get_layers(service)

    return chain.from_iterable(
        layer.QueryLayer(Geometry=mend(layers[layer].extent))
        for layer in requested_layers
    )


def pairs(iterator):
    """
    Returns the items in the iterator pairwise, like so;

    >>> list(pairs([0, 1, 2]))
    [(0, 1), (1, 2)]
    """
    first, second = tee(iterator)
    next(second)
    yield from zip(first, second)


def get_paths(request_layers):
    paths = get_data(request_layers)
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
