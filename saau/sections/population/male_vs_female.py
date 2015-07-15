import pandas

from ..image_provider import ImageProvider
from ..abs import abs_obtain_data

obtain_url = (
    'http://stat.abs.gov.au/'
    'FileView2.aspx?IDFile=66a73a96-49f1-4445-9145-300eede1c891'
)
filename = 'gendered_populations.csv'


class MaleVSFemaleImageProvider(ImageProvider):
    def has_required_data(self):
        return self.data_dir_exists(filename)

    def obtain_data(self):
        return abs_obtain_data(
            self,
            obtain_url,
            filename
        )

    def build_image(self, output_filename):
        BULLSHIT_LOCATIONS = {
            'Unincorporated NT', 'No usual address (NT)',
            'Unincorporated ACT', 'No usual address (ACT)',
            'Unincorp. Other Territories', 'No usual address (OT)'
        }

        df = pandas.read_csv(
            self.data_dir_join(filename),
            usecols=[
                'Age',
                'Time',      # will be filtered and removed
                'LGA 2013',  # will be remapped to location
                'Value',
                'Sex'
            ]
        )

        df = df[~(
            (df.Sex == 'Persons') |
            (df.Value == 0) |
            df['LGA 2013'].isin(BULLSHIT_LOCATIONS)
        )]

        df.Sex = df.Sex.astype('category')
        df = df[df.pop('Time') == 2013]
        df.rename(columns={'LGA 2013': 'Location'}, inplace=True)

        # gender = lambda g: df[df.Sex == g]

        # import IPython
        # IPython.embed()

        return False
