"""
http://stat.abs.gov.au/Index.aspx?DataSetCode=ABS_CENSUS2011_T09_LGA
"""
IMAGES = ['german.GermanAncestryImageProvider']

from ...utils.download.abs import get_generic_data


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
    assert country in MAP
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
