from operator import itemgetter
from itertools import chain
from typing import List

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


def get_data(requested_layers: List[str]):
    catalog = Catalog('http://services.ga.gov.au/site_7/rest/services')
    service = catalog['NM_Transport_Infrastructure']
    layers = get_layers(service)

    return chain.from_iterable(
        layers[layer].QueryLayer(Geometry=mend_extent(layers[layer].extent))
        for layer in requested_layers
    )


def get_paths(request_layers: List[str]) -> np.array:
    paths = get_data(request_layers)
    paths = map(itemgetter('geometry'), paths)
    paths = chain.from_iterable(
        geometry.paths
        for geometry in paths
        if hasattr(geometry, 'paths')
    )

    return np.array([
        tuple(
            (part.x, part.y)
            for part in path
        )
        for path in paths
    ])
