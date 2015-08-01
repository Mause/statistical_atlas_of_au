import requests

from . import TransportationImageProvider
from ..shapely_utils import boundary_to_polygon, raw_boundary_to_polygon
from ..aus_map import AUS_NW, AUS_SE
from ..misc.header import render_header_to

PATH = 'ferry_paths.json'
BASE = 'http://journeyplanner.silverrailtech.com/JourneyPlannerService/V2/REST'
API_KEY = 'eac7a147-0831-4fcf-8fa8-a5e8ffcfa039'
AUSTRALIA_BOUNDARY = raw_boundary_to_polygon([AUS_NW, AUS_SE])


def query(endpoint, params):
    return requests.get(
        BASE + endpoint,
        params=dict(params, ApiKey=API_KEY)
    )


def get_datasets():
    r = query(
        '/Datasets',
        {'format': 'json'}
    )
    return r.json()["AvailableDataSets"]


def show(ax, poly, color):
    import numpy as np
    ppoints = np.array(poly.boundary.coords[:])
    ax.scatter(
        ppoints[::, 0], ppoints[::, 1],
        color=color
    )


def get_australian_dataset_names():
    for dataset in get_datasets():
        boundary = dataset["BoundaryPolyline"]
        boundary = boundary_to_polygon(boundary, True)

        # import matplotlib.pyplot as plt
        # print(dataset['Id'])
        # ax = plt.gca()
        # show(ax, boundary, 'red')
        # show(ax, AUSTRALIA_BOUNDARY, 'blue')
        # plt.savefig('{}.png'.format(dataset['Id']))
        # ax.clear()

        if AUSTRALIA_BOUNDARY.intersects(boundary):
            yield dataset['Id']


def get_mapping_data(dataset, route):
    return query(
        "/DataSets/{}/RouteMap".format(dataset),
        {
            'Route': route,
            'MappingDataRequired': True,
            'transactionId': 0,
            'format': 'json'
        }
    ).json()


def obtain_data():
    dataset_names = list(get_australian_dataset_names())

    for dataset in dataset_names:
        r = query(
            '/Datasets/{}/Stops'.format(dataset),
            {
                'transportModes': 'Ferry',
                'format': 'json',
                'searchTerm': 'Ferry'
            }
        )

        # routeTimetableGroupUid = 'PerthRestricted:3'
        for transit_stop in r.json()['TransitStops']:
            if 'Ferry' not in transit_stop['SupportedModes']:
                continue

            for route in transit_stop['Routes'].split(';'):
                data = get_mapping_data(dataset, route)

                for path in data['MapSegments']:
                    yield [
                        tuple(map(float, point.split(',')))
                        for point in path['Polyline'].split(';')
                    ]


class FerryImageProvider(TransportationImageProvider):
    path = PATH

    def obtain_data(self):
        return self.save_json(
            PATH,
            list(obtain_data())
        )

    def build_image(self, q):
        fig = super().build_image(q)

        return render_header_to(
            fig,
            19.25,
            'From SilverRails Tech',
            'Ferry routes in Australia',
        )
