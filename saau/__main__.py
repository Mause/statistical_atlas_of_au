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


STATS_DATA = 'd:\\stats_data'
CACHE = join(STATS_DATA, 'cache')
OUTPUT = join(STATS_DATA, 'output')
HERE = dirname(__file__)
logging.basicConfig(level=logging.DEBUG)
sys.path.insert(0, expanduser('~/Dropbox/temp/arcrest'))

from .sections import aus_map, towns
from .utils import get_name
from .sections.shape import ShapeFileNotFoundException

import matplotlib.pyplot as plt
from betamax import Betamax


with Betamax.configure() as conf:
    conf.cassette_library_dir = join(CACHE, 'cassettes')


def dir_for_thing(thing):
    not_class = isinstance(thing, types.ModuleType)

    import_path = thing.__name__ if not_class else thing.__module__

    return join(*import_path.split('.')[:3])


def build_tree(root, packages):
    for package in packages:
        os.makedirs(join(root, dir_for_thing(package)), exist_ok=True)


def ensure_data(prov):
    """
    Given that `prov`
    """
    if not prov.has_required_data() and hasattr(prov, 'obtain_data'):
        try:
            val = prov.obtain_data()
        except Exception as e:
            logging.exception(e)
            return False

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

    packages = pkgutil.walk_packages(
        [dirname(__file__)],
        prefix='saau.',
        onerror=logging.error
    )

    packages = [
        loader.find_module(name).load_module()
        for loader, name, _ in packages
        if name.startswith('saau.sections.')
    ]

    top_level = [
        package
        for package in packages
        if package.__name__.count('.') == 2
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

    yield from load_classes(load_submodules(image_providers))


def load_classes(modules):
    for module, classname in modules:
        try:
            yield getattr(module, classname)
        except AttributeError:
            logging.error(
                "Couldn't load class \"%s\"",
                module.__name__ + '.' + classname
            )


def load_submodules(image_providers):
    for package, submodule, classname in image_providers:
        try:
            yield (
                importlib.import_module('.' + submodule, package.__package__),
                classname
            )
        except ImportError:
            logging.error(
                "Couldn't load module \"%s\"",
                package.__package__ + '.' + submodule
            )


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
    image_providers = list(load_image_providers(args.filter))

    logging.info('Building directories')
    build_tree(CACHE, image_providers)
    build_tree(OUTPUT, image_providers)

    logging.info('Downloading requisite data')

    # TODO: services architecture
    data_dir = join(CACHE, 'aus_map')
    os.makedirs(data_dir, exist_ok=True)
    assert ensure_data(aus_map.AusMap(data_dir))

    data_dir = join(CACHE, 'towns')
    os.makedirs(data_dir, exist_ok=True)
    assert ensure_data(towns.TownsData(data_dir))

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
            OUTPUT,
            dir_for_thing(prov),
            '{}.png'.format(prov.__module__.split('.')[-1])
        )
        if exists(output_filename):
            if rerender_all:
                move_old(output_filename)
            else:
                continue

        try:
            logging.info('Building graph for %s', get_name(prov))
            fig = prov.build_image(output_filename)
            logging.info('Rendering %s', get_name(prov))
            try:
                fig.savefig(output_filename)
            except AttributeError:
                fig.figure.savefig(output_filename)
            plt.close('all')  # don't allow an old image to affect a new one

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
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='Just list all of the available image providers'
    )
    return parser.parse_args()


def main():
    args = get_args()

    if args.list:
        image_providers = load_image_providers(args.filter)
        for ip in image_providers:
            logging.info(' * %s', get_name(ip))
    else:
        image_providers = setup(args)
        build_images(image_providers, args.rerender)


if __name__ == '__main__':
    main()
