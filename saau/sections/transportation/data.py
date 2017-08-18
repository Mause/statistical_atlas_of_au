from operator import attrgetter, itemgetter
from itertools import chain, tee

import sys
sys.path.insert(0, 'C:\\Users\\Dominic\\Dropbox\\temp\\arcrest')

from arcrest import Catalog
import numpy as np


def get_layers(service):
    layers = service.layers
    return {
        layer.name: layer
        for layer in layers
    }


def mend_extent(extent):
    extent.wkid = extent.spatialReference.wkid
    return extent


def get_data(requested_layers):
    catalog = Catalog('http://services.ga.gov.au/site_7/rest/services')
    service = catalog['NM_Transport_Infrastructure']
    layers = get_layers(service)

    return chain.from_iterable(
        layers[layer].QueryLayer(Geometry=mend_extent(layers[layer].extent))
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
