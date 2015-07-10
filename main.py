import sys
from os.path import expanduser
sys.path.insert(0, expanduser('~/Dropbox/temp/arcrest'))

import os
import types
import logging
import pkgutil
import argparse
import importlib
from fnmatch import fnmatch
from os.path import join, dirname, exists, basename
logging.basicConfig(level=logging.DEBUG)

import sections.aus_map
from utils import get_name
from sections.shape import ShapeFileNotFoundException

from betamax import Betamax

HERE = dirname(__file__)
CACHE = 'd:\\stats_data\\cache'


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
        assert val in {True, False}, prov  # ensure an explicit value

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
    # from concurrent.futures import ThreadPoolExecutor
    # map = ThreadPoolExecutor(10).map
    return list(filter(ensure_data, image_providers))



def build_images(image_providers):
    logging.info('Rendering images')
    for prov in image_providers:
        logging.info('Rendering %s', prov)

        try:
            output_filename = join(
                'output',
                dir_for_thing(prov),
                '{}.png'.format(prov.__module__.split('.')[-1])
            )
            if exists(output_filename):
                continue
            prov.build_image(output_filename)

        except NotImplementedError:
            logging.info("Can't render %s", get_name(prov))

        except ShapeFileNotFoundException:
            logging.info(
                "Can't render %s; couldn't access required data",
                get_name(prov)
            )


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--filter')
    return parser.parse_args()


def main():
    args = get_args()

    image_providers = setup(args)

    build_images(image_providers)


if __name__ == '__main__':
    main()
