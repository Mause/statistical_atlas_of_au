from . import TransportationImageProvider


class RoadImageProvider(TransportationImageProvider):
    path = 'road_paths.json'
    layers = ['All_Roads', 'Major_Road_Network']
