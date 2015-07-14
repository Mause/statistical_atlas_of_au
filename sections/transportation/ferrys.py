import requests

from ..image_provider import ImageProvider

PATH = 'ferry_paths.json'
BASE = 'http://journeyplanner.silverrailtech.com/JourneyPlannerService/V2'
DATASET = 'PerthRestricted'


class FerryImageProvider(ImageProvider):
    def has_required_data(self):
        return self.data_dir_exists(PATH)

    def obtain_data(self):

        url = BASE + "/rest/DataSets/{dataset}/RouteMap".format_map(locals())

        api_key = "eac7a147-0831-4fcf-8fa8-a5e8ffcfa039"

        routeTimetableGroupUid = 'PerthRestricted:3'
        r = requests.get(
            url,
            params={
                'ApiKey': api_key,
                'Route': routeTimetableGroupUid,
                'MappingDataRequired': True,
                'transactionId': 0,
                'format': 'json'
            }
        )
        data = r.json()

        return self.save_json(
            PATH,
            [
                [
                    tuple(map(float, point.split(',')))
                    for point in path['Polyline'].split(';')
                ]
                for path in data['MapSegments']
            ]
        )
