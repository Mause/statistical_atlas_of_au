'''
ABS_CENSUS2011_B13_LGA

Estimated Resident Population by Sex by Age Group by LGA, 2001-2013 on
ASGS 2013  MetaData : ERP by LGA (ASGS 2013)
'''

import logging

import cartopy.crs as ccrs
from matplotlib import patches as mpatches
from matplotlib.colors import ListedColormap

from ..image_provider import ImageProvider
from ...utils.download.abs import get_generic_data, abs_data_to_dataframe
from ...utils.header import render_header_to

FILENAME = 'gendered_populations.csv'
SEXES = ['Males', 'Females']


COLOR_RANGE_HEX = [
    '#426673',
    '#899A91',
    '#F0E3B6',
    '#CC8A6E',
    '#B03F41'
]
COLOR_RANGE = ListedColormap(COLOR_RANGE_HEX, 'MaleVSFemale')


class MaleVSFemaleImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(FILENAME)

    def obtain_data(self):
        data = get_generic_data(
            'ABS_ERP_LGA',
            and_=[
                'FREQUENCY.A',
                'AGE.TT',
                # 'STATE.0',
                'MEASURE.1',
                'REGIONTYPE.LGA2011'
            ]
            # frequency, age, sex, measure, lga_region
        )
        return self.save_json(FILENAME, data)

    def load_data(self):
        df = abs_data_to_dataframe(self.load_json(FILENAME))

        df.SEX = (
            df.SEX
            .replace(
                [1, 2, 3],
                ['Males', 'Females', 'Persons']
            )
            .astype('category')
        )
        df.rename(columns={
            'LGA_REGION': 'Location',
            'SEX': 'Sex'
        }, inplace=True)

        df = df[~(
            (df.Sex == 'Persons') |
            (df.Value == 0)
        )]
        df = df[df.pop('Time') == 2013]

        return df

    def render_map(self, data):
        logging.info('Building map')

        aus_map = self.services.aus_map.get_map()  # (zorder=10)
        logging.info('Map built')

        logging.info('Adding data for %d towns to map', len(data))

        for cl, pc_diff in data:
            aus_map.add_geometries(
                [d.geometry for d in cl.rec],
                facecolor=COLOR_RANGE(pc_diff),
                edgecolor='grey',
                linewidth=0.125,
                crs=ccrs.PlateCarree(),
                zorder=5
            )

        logging.info('Adding legend')
        aus_map.figure.legend(
            [
                mpatches.Rectangle((0, 0), 1, 1, facecolor=col)
                for col in COLOR_RANGE_HEX
            ],
            ['-10', '-5', '0', '5', '10'],
            title='PERCENT MORE'
        )
        return aus_map

    def build_image(self):
        df = self.load_data()
        logging.info('Data for %d towns available', len(df))

        logging.info("Classifying population data")
        data = []

        get_shape = lambda lga: self.services.lga.get('LGA_CODE11', lga)

        for location in df.Location.unique():
            rel = df[df.Location == location]
            # there is some weird duplication in the dataset,
            # so we just get the highest value for each sex
            rel = {
                sex: rel[rel.Sex == sex].Value.max()
                for sex in SEXES
            }
            # negative here means more females, otherwise more males
            pc_diff = (rel['Males'] / rel['Females'] * 100) - 100
            data.append((
                get_shape(location),
                pc_diff
            ))

        aus_map = self.render_map(data)

        return render_header_to(
            self.services.fonts.get_font(),
            aus_map,
            19.25,
            lines=[
                '<b><t>MAP OF</t></b>',
                '<b>PREDOMINATING SEX</b>',
                'SHOWING THE EXCESS OF MALES OR OF FEMALES',
                'IN THE DISTRIBUTION OF POPULATION OVER COUNTRY AREA',
                '<i>Compiled using estimates from the ABS Census Data 2011</i>'
            ]
        )
