import os
import sys
import types
import logging
import pkgutil
import warnings
import argparse
import importlib
from glob import iglob as glob
from fnmatch import fnmatch
from operator import itemgetter
from concurrent.futures import ThreadPoolExecutor
from os.path import join, dirname, exists, basename, splitext, expanduser

CACHE = 'd:\\stats_data\\cache'
HERE = dirname(__file__)
logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, expanduser('~/Dropbox/temp/arcrest'))

import sections.aus_map
from utils import get_name
from sections.shape import ShapeFileNotFoundException

from betamax import Betamax


with Betamax.configure() as conf:
    conf.cassette_library_dir = join(CACHE, 'cassettes')


def dir_for_thing(thing):
    not_class = isinstance(thing, types.ModuleType)

    import_path = thing.__name__ if not_class else thing.__module__

    return join(*import_path.split('.')[:2])


def build_tree(root, packages):
    for package in packages:
        os.makedirs(join(root, dir_for_thing(package)), exist_ok=True)


def ensure_data(prov):
    """
    Given that `prov`
    """
    if not prov.has_required_data() and hasattr(prov, 'obtain_data'):
        val = prov.obtain_data()

        if val not in {True, False}:
            warnings.warn(
                '{}.obtain_data() should return an explicit boolean value'
                .format(get_name(prov))
            )

        if not val:
            logging.warning("Couldn't obtain data for %s", get_name(prov))

        return val
    return True


def load_image_providers(filter_pattern):
    """
    Loads image providing modules in submodules of `sections`.
    Said image providers are declared in an `IMAGES` list variable on the
    submodule of `sections`
    """

    logging.info('Loading packages')
    packages = [
        loader.find_module(name).load_module()
        for loader, name, _ in pkgutil.walk_packages(['.'])
        if name.startswith('sections.')
    ]

    top_level = [
        package
        for package in packages
        if package.__name__.count('.') == 1
        and basename(package.__file__) == '__init__.py'
    ]

    if not filter_pattern:
        matcher = lambda _: True
    else:
        logging.info(
            "Filtering image providers by \"%s\"",
            filter_pattern
        )
        matcher = lambda prov: fnmatch(prov, filter_pattern)

    image_providers = [
        (package,) + tuple(image_provider.split('.'))
        for package in top_level
        for image_provider in package.IMAGES
        if matcher(image_provider)
    ]

    logging.info('Loading image providers')
    return [
        getattr(
            importlib.import_module(
                '.' + submodule,
                package.__package__
            ),
            classname
        )
        for package, submodule, classname in image_providers
    ]


def threaded_filter(predicate, iterable):
    # for each item in the iterable, determine is we should keep it
    iterable = ThreadPoolExecutor(10).map(
        lambda thing: (predicate(thing), thing),
        iterable
    )
    # filter out those we don't want to keep
    iterable = filter(itemgetter(0), iterable)
    # grab the actual items
    return map(itemgetter(1), iterable)


def setup(args):
    image_providers = load_image_providers(args.filter)

    logging.info('Building directories')
    build_tree(CACHE, image_providers)
    build_tree(join(HERE, 'output'), image_providers)

    logging.info('Downloading requisite data')

    data_dir = join(CACHE, 'aus_map')
    os.makedirs(data_dir, exist_ok=True)
    ensure_data(sections.aus_map.AusMap(data_dir))

    image_providers = [
        prov(join(CACHE, dir_for_thing(prov)))
        for prov in image_providers
    ]

    # grab the data for each image_provider.
    # those that can't get their data, we filter out
    return list(filter(ensure_data, image_providers))


def move_old(filename):
    def get_rest(related):
        for rel in related:
            try:
                yield int(
                    rel.split('.')[-2]
                )
            except ValueError:
                pass

    name, ext = splitext(filename)
    related = max(
        get_rest(glob(name + '*')) or [],
        default=0
    )
    os.rename(
        filename,
        '{}.{}{}'.format(
            name,
            related + 1,
            ext
        )
    )


def build_images(image_providers, rerender_all=False):
    if rerender_all:
        logging.info('Rerendering all images')
    else:
        logging.info('Rendering images')

    for prov in image_providers:
        output_filename = join(
            'output',
            dir_for_thing(prov),
            '{}.png'.format(prov.__module__.split('.')[-1])
        )
        if exists(output_filename):
            if rerender_all:
                move_old(output_filename)
            else:
                continue

        try:
            logging.info('Rendering %s', get_name(prov))
            prov.build_image(output_filename)
            if exists(output_filename):
                logging.info('Render successful')

        except NotImplementedError:
            logging.exception("Can't render %s", get_name(prov))

        except ShapeFileNotFoundException:
            logging.info(
                "Can't render %s; couldn't access required data",
                get_name(prov)
            )

        del prov  # force cleanup
    logging.info('Done.')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-f', '--filter',
        help='Unix style globbing syntax for individual image providers'
    )
    parser.add_argument(
        '-r', '--rerender',
        action='store_true',
        help='Rerender all images'
    )
    return parser.parse_args()


def main():
    args = get_args()

    image_providers = setup(args)

    build_images(image_providers, args.rerender)


if __name__ == '__main__':
    main()
