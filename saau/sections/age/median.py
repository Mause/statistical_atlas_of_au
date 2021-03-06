import logging
from operator import itemgetter

from matplotlib.cm import get_cmap
import matplotlib as mpl
import cartopy.crs as ccrs

from ...utils.download.abs import get_generic_data, abs_data_to_dataframe
from ..image_provider import ImageProvider
from ...utils.header import render_header_to

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
                'REGIONTYPE.SA2',
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

    def region_lookup(self, sa3):
        return self.services.sa3.get('SA2_MAIN11', int(sa3))

    def build_image(self):
        colors = get_cmap('Purples')

        age_data = abs_data_to_dataframe(self.load_json(FILENAME))
        age_data = [
            (
                self.region_lookup(data_point.REGION),
                data_point.Value
            )
            for _, data_point in age_data.iterrows()
        ]

        values = list(map(itemgetter(1), age_data))
        norm = mpl.colors.Normalize(
            vmin=min(values),
            vmax=max(values)
        )
        logging.info(
            '%d -> %d',
            min(values),
            max(values)
        )

        aus_map = self.services.aus_map.get_map()
        for shapes, mage in age_data:
            aus_map.add_geometries(
                [
                    shape.geometry
                    for shape in shapes.rec
                    if shape.geometry
                ],
                crs=ccrs.PlateCarree(),
                color=colors(norm(mage))
            )

        cax = aus_map.figure.add_axes([0.95, 0.2, 0.02, 0.6])
        cb = mpl.colorbar.ColorbarBase(
            cax,
            cmap=colors,
            norm=norm,
            spacing='props'
        )
        cb.set_label('Average age')

        return render_header_to(
            self.services.fonts.get_font(),
            aus_map,
            19.25,
            [
                "<b>MAP</b>",
                "SHOWING THE DISTRIBUTION OF",
                "<b>MEDIAN AGE</b>",
                "<i>Compiled using data from the 2011 Australian Census</i>"
            ]
        )
