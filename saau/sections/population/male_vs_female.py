'''
ABS_CENSUS2011_B13_LGA

Estimated Resident Population by Sex by Age Group by LGA, 2001-2013 on ASGS 2013  MetaData : ERP by LGA (ASGS 2013)
'''

import logging

import pandas
import cartopy.crs as ccrs
from matplotlib import patches as mpatches
from matplotlib.colors import ListedColormap

from ..aus_map import get_map
from ..image_provider import ImageProvider
from ..abs import get_generic_data, collapse_concepts
from ..towns import get_towns, TownsData

OBTAIN_URL = (
    'http://stat.abs.gov.au/'
    'FileView2.aspx?IDFile=66a73a96-49f1-4445-9145-300eede1c891'
)
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
BULLSHIT_LOCATIONS = {
    'Unincorporated NT', 'No usual address (NT)',
    'Unincorporated ACT', 'No usual address (ACT)',
    'Unincorp. Other Territories', 'No usual address (OT)'
}


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
                # 'REGIONTYPE.LGA2011'
            ]
            # frequency, age, sex, measure, lga_region
        )
        return self.save_json(FILENAME, data)

    def load_data(self):
        data = self.load_json(FILENAME)['series']
        data = (
            dict(thing, concepts=collapse_concepts(thing['concepts']))
            for thing in data
        )
        data = (
            dict(ob, **thing['concepts'])
            for thing in data
            for ob in thing['observations']
        )

        df = pandas.DataFrame(data)

        # del df[['annotation', 'FREQUENCY', 'MEASURE', 'AGE']]
        df.SEX = (
            df.SEX
            .replace(
                ['1', '2', '3'],
                ['Males', 'Females', 'Persons']
            )
            .astype('category')
        )
        df.rename(columns={
            'LGA_REGION': 'Location',
            'SEX': 'Sex'
        }, inplace=True)

        integer_columns = ['Value', 'Time', 'Location']
        df[integer_columns] = df[integer_columns].astype(int)

        df = df[~(
            (df.Sex == 'Persons') |
            (df.Value == 0) |
            df.Location.isin(BULLSHIT_LOCATIONS)
        )]
        df = df[df.pop('Time') == 2013]

        return df

    def render_map(self, data, towns):
        logging.info('Building map')

        aus_map = get_map()  # (zorder=10)
        logging.info('Map built')

        logging.info('Adding data for %d towns to map', len(data))

        for cl, pc_diff in data:
            aus_map.add_geometries(
                [towns[cl].geometry],
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

    def build_image(self, output_filename):
        df = self.load_data()
        logging.info('Data for %d towns available', len(df))

        logging.info('Loading towns')
        towns = get_towns()
        logging.info('Towns loaded')

        logging.info("Classifying population data")
        data = []

        td = TownsData.instance()
        unlocatable = 0
        for location in df.Location.unique():
            try:
                clean_location = td.lga_to_lga_name(
                    location
                ).rpartition(' ')[0]
            except KeyError:
                unlocatable += 1
                continue
            if clean_location not in towns:
                unlocatable += 1
                continue

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
                clean_location,
                pc_diff
            ))

        # import numpy as np
        # import matplotlib.pyplot as plt
        # ddata = np.array(data)

        # plt.bar(
        #     ddata[::, 1].astype(float),
        #     np.arange(len(ddata)),
        # )
        # plt.show()

        assert len(data)
        logging.info('unlocatable -> %d', unlocatable)

        aus_map = self.render_map(data, towns)

        # aus_map.set_title('Male VS Female Population')

        from ..misc.header import render_header_to

        return render_header_to(
            aus_map,
            19.25,
            lines=[
                '<b><t>MAP OF</t></b>',
                '<b>Predominating Sex</b>',
                'SHOWING THE EXCESS OF MALES OR OF FEMALES',
                'IN THE DISTRIBUTION OF POPULATION OVER COUNTRY AREA',
                '<i>Compiled using estimates from the ABS Census Data 2011</i>'
            ]
        )
