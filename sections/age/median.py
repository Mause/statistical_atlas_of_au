import json

from ..towns import get_towns
from ..aus_map import get_map
from ..abs import get_generic_data
from ..image_provider import ImageProvider

DATASETID = 'ABS_CENSUS2011_B02'
FILENAME = 'median_ages.json'


class MedianAgeImageProvider(ImageProvider):
    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        data = get_generic_data(
            DATASETID,
            and_=[
                'FREQUENCY.A',
                'STATE.0',
                'REGIONTYPE.SA3',
                'MEASURE.MAGE'
            ]
        )
        with open(self.data_dir_join(FILENAME), 'w') as fh:
            json.dump(data, fh, indent=4)

        return True
