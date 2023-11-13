from operator import itemgetter
from itertools import chain
from typing import List
from functools import cache

from arcrest import Catalog
import numpy as np
from tqdm import tqdm


@cache
def get_layers():
    catalog = Catalog('http://services.ga.gov.au/site_7/rest/services')
    service = catalog['NM_Transport_Infrastructure']
    layers = service.layers
    return {
        layer.name: layer
        for layer in layers
    }


def mend_extent(extent):
    extent.wkid = extent.spatialReference.wkid
    return extent


def get_data(requested_layers: List[str]):
    layers = get_layers()
    return chain.from_iterable(
        layers[layer].QueryLayer(Geometry=mend_extent(layers[layer].extent))
        for layer in tqdm(requested_layers, desc='Fetching requested layers')
    )


def get_paths(request_layers: List[str]) -> np.array:
    paths = get_data(request_layers)
    paths = map(itemgetter('geometry'), paths)
    paths = chain.from_iterable(
        geometry.paths
        for geometry in paths
        if hasattr(geometry, 'paths')
    )

    result = [
        tuple(
            (part.x, part.y)
            for part in path
        )
        for path in paths
    ]

    return result # np.array(result)
