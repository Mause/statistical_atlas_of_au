from matplotlib.cm import get_cmap
import cartopy.crs as ccrs

from ..towns import get_towns, TownsData
from ..aus_map import get_map
from ..abs import get_generic_data, collapse_concepts
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
                'REGIONTYPE.SA3',
                'MEASURE.MAGE'
            ],
            or_=[
                'STATE.0',
                'STATE.1',
                'STATE.2',
                'STATE.3',
                'STATE.4',
                'STATE.5',
                'STATE.6',
                'STATE.7',
                'STATE.8',
                'STATE.9'
            ]
        )
        assert data['series']

        return self.save_json(FILENAME, data)

    def build_image(self, _):
        aus_map = get_map()
        towns = get_towns()
        colors = get_cmap('Purples')

        age_data = self.load_json(FILENAME)
        age_data = [
            dict(
                collapse_concepts(data_point['concepts']),
                **data_point['observations'][0]
            )
            for data_point in age_data['series']
        ]

        region_lookup = TownsData.instance().sla_to_sla_name

        __import__('ipdb').set_trace()

        for data_point in age_data:
            try:
                town_name = region_lookup(data_point['REGION'])
            except KeyError:
                continue

            aus_map.add_geometries(
                [towns[town_name].geometry],
                crs=ccrs.PlateCarree(),
                color=colors(data_point['MAGE'])
            )

        return aus_map
