from os.path import basename, splitext

import pandas
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from ..image_provider import ImageProvider
from ...utils.download import get_abs_csv

url = (
    'http://www.ausstats.abs.gov.au/Ausstats/subscriber.nsf/'
    '0/795163C2711B071BCA257E7000151A77/'
    '$File/1379055001_industry_2009-2013_lga_201506.zip'
)
filename = splitext(basename(url))[0] + '.csv'

STATES = {
    0: "Australia",
    1: "New South Wales",
    2: "Victoria",
    3: "Queensland",
    4: "South Australia",
    5: "Western Australia",
    6: "Tasmania",
    7: "Northern Territory",
    8: "Australian Capital Territory",
    9: "Other Territories",
}
STATES_R = {v: k for k, v in STATES.items()}
INDUSTRIES = [
    # 'Accommodation & Food Services (%) (Percent)',
    # 'Electricity, Gas, Water & Waste Services (%) (Percent)',
    # 'Mining (%) (Percent)',
    # 'Total employed (no.) (Persons)',
    'Administrative & Support Services (%) (Percent)',
    'Agriculture, Forestry and Fishing (%) (Percent)',
    'Arts & Recreation Services (%) (Percent)',
    'Construction (%) (Percent)',
    'Education & Training (%) (Percent)',
    'Financial & Insurance Services (%) (Percent)',
    'Health Care & Social Assistance (%) (Percent)',
    'Information Media & Telecommunications (%) (Percent)',
    'Manufacturing (%) (Percent)',
    'Other services (%) (Percent)',
    'Professional Scientific & Technical Services (%) (Percent)',
    'Public Administration & Safety (%) (Percent)',
    'Rental, Hiring, & Real Estate Services (%) (Percent)',
    'Retail Trade (%) (Percent)',
    'Transport, Postal and Warehousing (%) (Percent)',
    'Wholesale Trade (%) (Percent)',
]
COLORS = [
    "#7d7af3",
    "#f3da7a",
    "#967af3",
    "#f3ae7a",
    "#f3c07a",
    "#f37a86",
    "#7af3d7",
    "#f3e37a",
    "#c27af3",
    "#8cf37a",
    "#f3e07a",
    "#7af3df",
    "#f37acd",
    "#83f37a",
    "#7a86f3",
    "#f37a92",
    "#7af3f0",
    "#f3907a",
    "#7af3a5",
    "#be7af3"
]


class IndustryImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(filename)

    def obtain_data(self):
        return get_abs_csv(
            url,
            self.data_dir_join(filename)
        )

    def load_data(self):
        df = (
            pandas
            .read_csv(
                self.data_dir_join(filename),
                encoding='latin-1'
            )
            .convert_objects(convert_numeric=True)
            .rename(columns={
                'Year - Labels': 'Year',
                'LGA 2013 - Codes': 'LGA_CODE',
                'LGA 2013 - Labels': 'LGA_LABEL'
            })
        )
        for key in df:
            if key.startswith('REGISTERED MOTOR VEHICLES - '):
                del df[key]
        return df.rename(columns={
            k: (
                k.split('-')[1].strip() if '-' in k
                else k
            )
            for k in df
        })

    def get_state_code(self, lga_code):
        codes = self.services.lga.get('LGA_CODE11', lga_code).STATE_CODE
        return None if codes.empty else codes.item()

    def build_image(self):
        data = self.load_data()
        data = data[data.Year == 2013]

        # preload reference
        self.services.lga.load_reference()

        data['state'] = pandas.Series(
            data.LGA_CODE.map(self.get_state_code),
            index=data.index
        )

        data = {
            state: data[data.state == state_num][INDUSTRIES].sum()
            for state_num, state in STATES.items()
            if state != 'Australia'
        }

        fig, ax = plt.subplots(nrows=3, ncols=3)

        for idx, state in enumerate(sorted(data.keys())):
            subax = ax.flat[idx]

            rows = data[state]
            subax.bar(
                np.arange(len(rows)),
                rows.values,
                color=COLORS
            )

            subax.set_title(state)
            subax.set_xticklabels([])

        fig.legend(
            [
                mpatches.Rectangle((0, 0), 1, 1, facecolor=color)
                for color in COLORS
            ],
            INDUSTRIES,
            title='Industries'
        )

        fig.tight_layout(h_pad=0.5)
        fig.set_size_inches(16, 9)

        return fig
