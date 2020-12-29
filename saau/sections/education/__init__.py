from ..image_provider import ImageProvider
from ...utils.download.abs import abs_data_to_dataframe, get_generic_data

IMAGES = [
    'highschool.HighSchoolEducationImageProvider',
    'bachelors.BachelorsEducationImageProvider'
]

TYPP_MAP = {
    "Aged 15-24 years": ["40_2_T15", "40_3_T15", "50_2_T15", "50_3_T15"],
    "Aged 25 years and over": [
        "40_2_25OV", "40_3_25OV", "50_2_25OV", "50_3_25OV"
    ],
    "Catholic": ["22", "32"],
    "Full-time student": ["60_2", "40_2", "50_2"],
    "Full/Part-time student status not stated": ["40Z", "50Z", "60Z"],
    "Government": ["21", "31"],
    "Infants/Primary Total": "2",
    "Other Non Government": ["23", "33"],
    "Part-time student": ["60_3", "40_3", "50_3"],
    "Pre-school": "10",
    "Total": "TOT",
    "Type of educational institution not stated": "Z",
    "Other type of educational institution Total": "60",
    "Secondary Total": "3",
    "Technical or Further Educational Institution(a) Total": "40",
    "University or other Tertiary InstitutionTotal": "50"
}


class EducationImageProvider(ImageProvider):

    def has_required_data(self):
        return self.data_dir_exists(self.filename)

    def obtain_data(self):
        return self.save_json(
            self.filename,
            get_generic_data(
                'ABS_CENSUS2011_B15_LGA',
                and_=[
                    'FREQUENCY.A',
                    'REGIONTYPE.LGA2011',
                    'TYPP.{}'.format(self.school_type)
                ]
            )
        )

    def build_image(self):
        data = abs_data_to_dataframe(
            self.load_json(self.filename),
            ['FREQUENCY', 'Time', 'TYPP']
        )

        return self.services.aus_map.plot_abs(
            data,
            cmap='Reds'
        )
