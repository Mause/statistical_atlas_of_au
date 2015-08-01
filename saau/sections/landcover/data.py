import logging
import pickle
from itertools import count
from os.path import join, exists, basename

from ..image_provider import ImageProvider
from ..shape import shape_from_zip
from ..download import get_binary

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

        # stealing some logic from cartopy's shape.records()
        field_names = [field[0] for field in shape._reader.fields[1:]]
        geometry_factory = shape._geometry_factory

        for idx, thing in zip(count(), shape._reader.iterShapeRecords()):
            # geometry_factory is expensive, so we delay its use :P
            yield dict(
                zip(field_names, thing.record),
                geom=lambda: geometry_factory(thing.shape)
            )

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
        return all(map(self.data_dir_exists, FILENAMES))

    def get_needed(self):
        return [
            (url, filename)
            for url, filename in zip(DATA_URLS, FILENAMES)
            if not self.data_dir_exists(filename)
        ]

    def obtain_data(self):
        for url, filename in self.get_needed():
            get_binary(url, self.data_dir_join(filename))

        return not self.get_needed()
