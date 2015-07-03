from . import TransportationImageProvider


class RailroadImageProvider(TransportationImageProvider):
    path = 'railroad_paths.json'
    layers = ['Railways']
