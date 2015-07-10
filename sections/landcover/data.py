import logging
import pickle
from itertools import count
from os.path import join, exists, basename

import requests

from ..image_provider import ImageProvider
from ..shape import shape_from_zip

DATA_URLS = [
    "http://data.daff.gov.au/data/warehouse/lusag4l___001/SA_shape.zip",
    "http://data.daff.gov.au/data/warehouse/luvicg2ev__002/"
    "VLUIS_2010_v4_convertedtoALUM_201409.zip",
    "http://www.daff.gov.au/abares/aclump/Documents/"
    "tas-land-use-summer-2009-10-geodatabase.zip",
    "http://www.daff.gov.au/abares/aclump/Documents/Lump_BRS_11aug08_g94.zip",
    "http://www.daff.gov.au/abares/aclump/Documents/Southeast_SA_landuse.zip",
    "http://www.daff.gov.au/abares/aclump/Documents/WA_CapetoCape_landuse.zip",
    "http://www.daff.gov.au/abares/aclump/Documents/WA_shape.zip",
    "http://data.daff.gov.au/data/warehouse/lunswg1e___001/NSW_shape.zip",
]
FILENAMES = list(map(basename, DATA_URLS))
CACHE_FILENAME = 'cached_records.pickle'


def have_cached(data_dir):
    return exists(join(data_dir, CACHE_FILENAME))


def load_from_cache(data_dir):
    filename = join(data_dir, CACHE_FILENAME)
    with open(filename, 'rb') as fh:
        return pickle.load(fh)


def cache_data(data_dir, data):
    filename = join(data_dir, CACHE_FILENAME)
    with open(filename, 'wb') as fh:
        pickle.dump(data, fh)
    return data


def load_from_zips(data_dir):
    logging.info('Loading shapes')
    shapes = [
        shape_from_zip(join(data_dir, filename))
        for filename in FILENAMES
    ]
    logging.info('Building data frames')

    for shape in shapes:
        length = len(shape)
        logging.info('Yielding')
        for idx, record in zip(count(), shape.records()):
            attrs = {
                k: v.strip() if isinstance(v, (str, bytes))
                else v
                for k, v in record.attributes.items()
            }

            yield dict(attrs, geom=record.geometry)
            if idx % 1000 == 0:
                logging.info('%d/%d -> %f', idx, length, (idx / length * 100))
        logging.info('Scary')


def load_data(data_dir):
    if have_cached(data_dir):
        logging.info('Loading from cache')
        try:
            v = load_from_cache(data_dir)
            logging.info('Cache load successful')
            return v
        except EOFError:
            logging.info('Failed to load from cache, loading from zip')

    return cache_data(data_dir, list(load_from_zips(data_dir)))
    # frames = [
    #     pandas.DataFrame.from_records(
    #         dict(record.attributes, geom=geom)
    #         for record, geom in zip(shape.records(), shape.geometries())
    #     )
    #     for shape in shapes
    # ]

    # logging.info('Concatenating frames')
    # return pandas.concat(frames, ignore_index=True)


class LandcoverImageProvider(ImageProvider):
    def has_required_data(self):
        join_data_dir = lambda *args: join(self.data_dir, *args)
        return all(map(exists, map(join_data_dir, FILENAMES)))

    def obtain_data(self):
        needed = [
            (url, filename)
            for url, filename in zip(DATA_URLS, FILENAMES)
            if not exists(join(self.data_dir, filename))
        ]

        for url, filename in needed:
            r = requests.head(url)

            if 'Content-Length' in r.headers:
                import humanize
                logging.warning(
                    '%s is quite large at %s. '
                    'Considering downloading it manually?',
                    url,
                    humanize.naturalsize(int(r.headers['Content-Length']))
                )

            r = requests.get(url)

            with open(join(self.data_dir, filename), 'wb') as fh:
                fh.write(r.content)
