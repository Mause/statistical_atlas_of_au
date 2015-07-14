from functools import reduce

import pandas

from .aus_map import AusMap
from .shape import shape_from_zip


def get_towns():
    path = AusMap(None).data_dir_join('AUS_adm.zip')
    shire_data = shape_from_zip(path, 'AUS_adm2')

    return combine_towns({
        record.attributes['NAME_2'].strip(): record
        for record in shire_data.records()
    })


class DummyRecord:
    def __init__(self, attributes, geometry):
        self.attributes = attributes
        self.geometry = geometry


def combine_towns(towns):
    """
    Some towns are represented by multiple shapes;
    we combine them here
    """

    df_towns = pandas.DataFrame([
        dict(zip(['area_name', 'record'], pair))
        for pair in towns.items()
    ])

    to_mend_towns = set()
    for _, row in df_towns.iterrows():
        if '-' not in row.area_name:
            continue

        name = row.area_name.split('-')[0].strip()
        num = len(df_towns[df_towns.area_name.str.startswith(name)])
        if num > 1:
            to_mend_towns.add(name)

    for town in to_mend_towns:
        to_combine = df_towns[df_towns.area_name.str.startswith(town)]

        geometry = reduce(
            lambda a, b: a.union(b),
            [rec.geometry for rec in to_combine.record]
        )

        for _, row in to_combine.iterrows():
            if row.area_name in towns:
                del towns[row.area_name]

        towns[town] = DummyRecord({'NAME_2': town}, geometry)

    return towns
