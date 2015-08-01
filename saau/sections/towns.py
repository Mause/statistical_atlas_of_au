from functools import reduce

import pandas
import dill as pickle

from . import Singleton
from .aus_map import AusMap
from .image_provider import RequiresData
from .shape import shape_from_zip



def get_towns():
    return TownsData.instance().get_towns()


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


class TownsData(RequiresData, metaclass=Singleton):
    def __init__(self, data_dir):
        super().__init__(data_dir)

    def has_cached(self):
        return self.data_dir_exists('towns.pickle')

    def load_cached(self):
        with open(self.data_dir_join('towns.pickle'), 'rb') as fh:
            return pickle.load(fh)

    def cache(self, data):
        with open(self.data_dir_join('towns.pickle'), 'wb') as fh:
            pickle.dump(data, fh)
        return data

    def get_towns(self):
        if self.has_cached():
            return self.load_cached()

        else:
            path = AusMap.instance().data_dir_join('AUS_adm.zip')
            shire_data = shape_from_zip(path, 'AUS_adm2')

            val = combine_towns({
                record.attributes['NAME_2'].strip(): record
                for record in shire_data.records()
            })

        return self.cache(val)
