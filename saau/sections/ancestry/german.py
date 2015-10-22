# ancestry-german

from ..image_provider import ImageProvider
from . import get_data
from ...utils.download.abs import abs_data_to_dataframe

from matplotlib.cm import get_cmap
import matplotlib as mpl
import cartopy.crs as ccrs

FILENAME = 'german.json'


class GermanAncestryImageProvider(ImageProvider):
    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        return self.save_json(FILENAME, get_data('German'))

    def build_image(self):
        data = abs_data_to_dataframe(self.load_json(FILENAME))
        data = data[data.pop('Time') == 2011]
        del data['ANCP']
        del data['FREQUENCY']
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
