from functools import reduce
from os.path import basename, splitext
from zipfile import ZipFile
from functools import lru_cache
from io import BytesIO

import pandas
import requests
import dill as pickle

from ..sections.image_provider import RequiresData
from ..sections.shape import shape_from_zip
from ..sections.download import get_binary

DYNAMIC_TABLE = {
    'STATE_NAME_2011': 'state_name',
    'STATE_CODE_2011': 'state',
    'LGA_NAME_2011': 'lga_name',
    'LGA_CODE_2011': 'lga',
    'SLA_NAME_2011': 'sla_name',
    'SLA_MAINCODE_2011': 'sla'
}
DYNAMIC_TABLE_R = {v: k for k, v in DYNAMIC_TABLE.items()}


def get_towns():
    return TownsData.instance().get_towns()


class DummyRecord:
    def __init__(self, attributes, geometry):
        self.attributes = attributes
        self.geometry = geometry


def try_int(v):
    for func in (int, float):
        try:
            return func(v)
        except ValueError:
            pass

    return v


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


class LocationConversion(RequiresData):
    fmt = (
        'http://www.ausstats.abs.gov.au/Ausstats/subscriber.nsf/'
        '0/{}/$File/{}.zip'
    )

    urls = [
        fmt.format(
            '5CB0F0C29CC07051CA25791F000F2D3A',
            '12160_local_government_area_structure'
        ),

        fmt.format(
            'C468E0C71D4701D1CA257801000C6A58',
            '1270055001_sa3_2011_aust_csv'
        ),

        fmt.format(
            '0C1F9B2158B14477CA257801000C6A3B',
            '1270055001_sa2_2011_aust_csv'
        )
    ]
    filenames = [
        splitext(basename(url))[0] + '.csv'
        for url in urls
    ]

    def __init__(self, data_dir, services):
        assert data_dir, __import__('ipdb').set_trace()
        super().__init__(data_dir, services)

    @lru_cache()
    def load_reference(self):
        import pandas
        filenames = map(self.data_dir_join, self.filenames)
        frames = map(pandas.read_csv, filenames)
        return pandas.concat(list(frames), ignore_index=True)

    def has_required_data(self):
        return all(map(self.data_dir_exists, self.filenames))

    def obtain_data(self):
        return all(
            self.obtain_data_for_url(filename, url)
            for filename, url in zip(self.filenames, self.urls)
        )

    def obtain_data_for_url(self, filename, url):
        r = requests.get(url)
        assert r.ok, r.json()
        content = r.content

        with ZipFile(BytesIO(content)) as ziper:
            data = ziper.read(ziper.namelist()[0])

        with open(self.data_dir_join(filename), 'wb') as fh:
            fh.write(data)

        return self.data_dir_exists(filename)

    def __getattribute__(self, name):
        try:
            return super().__getattribute__(name)
        except AttributeError:
            pass

        if '_to_' in name:
            setattr(self, name, self._dynamic(name))

        return super().__getattribute__(name)

    def dynamic_by_name(self, ofrom_, oto_):
        ref = self.load_reference()
        try:
            ref[ofrom_], ref[oto_]
            from_, to_ = ofrom_, oto_
        except KeyError:
            from_, to_ = DYNAMIC_TABLE_R[ofrom_], DYNAMIC_TABLE_R[oto_]

        def wrapper(from_val):
            from_val = try_int(from_val)
            rows = ref[ref[from_] == from_val]
            try:
                return rows[to_].tolist()[0]
            except (KeyError, IndexError):
                raise KeyError((from_val, type(from_val))) from None

        wrapper.__doc__ = '{} to {}'.format(from_, to_)
        wrapper.__name__ = wrapper.__qualname__ = (
            '{}_to_{}'.format(ofrom_, oto_)
        )

        return wrapper

    def _dynamic(self, name):
        from_, to_ = name.split('_to_')
        return self.dynamic_by_name(from_, to_)


class TownsData(RequiresData):
    def __init__(self, data_dir, services):
        super().__init__(data_dir, services)
        self.conv = LocationConversion(data_dir)

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
            path = self.services.aus_map.data_dir_join('AUS_adm.zip')
            shire_data = shape_from_zip(path, 'AUS_adm2')

            val = combine_towns({
                record.attributes['NAME_2'].strip(): record
                for record in shire_data.records()
            })

        return self.cache(val)
