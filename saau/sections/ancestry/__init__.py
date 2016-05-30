"""
http://stat.abs.gov.au/Index.aspx?DataSetCode=ABS_CENSUS2011_T09_LGA
"""
IMAGES = [
    # 'american.AmericanAncestryImageProvider',
    'british.BritishAncestryImageProvider',
    'french.FrenchAncestryImageProvider',
    'german.GermanAncestryImageProvider',
    'irish.IrishAncestryImageProvider',
    'italian.ItalianAncestryImageProvider',
    'russian.RussianAncestryImageProvider',
]

from ..image_provider import ImageProvider
from ...utils.download.abs import get_generic_data, abs_data_to_dataframe

from matplotlib.cm import get_cmap
import matplotlib as mpl
import cartopy.crs as ccrs


MAP = {
    "Australian": 1101,
    "Australian Aboriginal": 1102,
    "Maori": 1201,
    "New Zealander": 1202,
    "English": 2101,
    "Scottish": 2102,
    "Welsh": 2103,
    "Irish": 2201,
    "Dutch": 2303,
    "French": 2305,
    "German": 2306,
    "Italian": 3103,
    "Maltese": 3104,
    "Spanish": 3106,
    "Croatian": 3204,
    "Greek": 3205,
    "Macedonian": 3206,
    "Serbian": 3213,
    "Hungarian": 3304,
    "Polish": 3307,
    "Russian": 3308,
    "Lebanese": 4106,
    "Turkish": 4907,
    "Vietnamese": 5107,
    "Filipino": 5201,
    "Chinese ": 6101,
    "Korean": 6902,
    "Indian": 7106,
    "Sinhalese": 7115,
    "South African": 9215
}


def get_data(country):
    assert country in MAP, country
    return get_generic_data(
        'ABS_CENSUS2011_T09_LGA',
        and_=[
            'FREQUENCY.A',
            # 'STATE.0',
            'REGIONTYPE.LGA2011',
            # 'MEASURE.TOT',
            'ANCP.{}'.format(MAP[country])
        ]
    )


class AncestryImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(self.filename)

    def obtain_data(self):
        return self.save_json(self.filename, get_data(self.ancestry_name))

    def build_image(self):
        data = abs_data_to_dataframe(
            self.load_json(self.filename),
            ['ANCP', 'FREQUENCY']
        )
        data = data[data.pop('Time') == 2011]
        del data['REGIONTYPE']

        lga_lookup = lambda code: self.services.lga.get('LGA_CODE11', code)

        aus_map = self.services.aus_map.get_map()
        colors = get_cmap('Purples')
        norm = mpl.colors.Normalize(
            vmin=data.Value.min(),
            vmax=data.Value.max()
        )

        for idx, loco in data.iterrows():
            aus_map.add_geometries(
                [
                    shape.geometry
                    for shape in lga_lookup(loco.REGION).rec
                    if shape.geometry
                ],
                crs=ccrs.PlateCarree(),
                color=colors(norm(loco.Value))
            )

        return aus_map
