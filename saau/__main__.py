import os
import sys
import types
import logging
import warnings
import argparse
import coloredlogs
from operator import itemgetter
from concurrent.futures import ThreadPoolExecutor as PoolExecutor
from os.path import join, dirname, exists, expanduser
from bdb import BdbQuit


STATS_DATA = 'c:\\stats_data'
CACHE = join(STATS_DATA, 'cache')
OUTPUT = join(STATS_DATA, 'output')
HERE = dirname(__file__)
coloredlogs.install(level='DEBUG')
sys.path.insert(0, expanduser('~/Dropbox/temp/arcrest'))

from .services import Services
from .utils import get_name, move_old
from .utils.shape import ShapeFileNotFoundException
from .loading import load_image_providers, load_service_providers

import matplotlib
matplotlib.use('Agg')
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
        logging.info('Obtaining data for %s', get_name(prov))
        try:
            val = prov.obtain_data()
        except BdbQuit:
            raise
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


def threaded_filter(predicate, iterable):
    # for each item in the iterable, determine is we should keep it
    iterable = PoolExecutor(10).map(
        lambda thing: (predicate(thing), thing),
        iterable
    )
    # filter out those we don't want to keep
    iterable = filter(itemgetter(0), iterable)
    # grab the actual items
    return map(itemgetter(1), iterable)


def initialize_providers(provs, services):
    return [
        prov(join(CACHE, dir_for_thing(prov)), services)
        for prov in provs
    ]


def setup(args):
    image_providers = list(load_image_providers(args.filter))

    logging.info('Building directories')
    build_tree(CACHE, image_providers)
    build_tree(OUTPUT, image_providers)

    logging.info('Setting up services')
    services_container = Services()

    services = list(load_service_providers(None))
    services = initialize_providers(services, services_container)
    build_tree(CACHE, services)
    ret = list(filter(ensure_data, services))
    services_container.inject(services)
    if not all(ret):
        logging.warning("Couldn't initialize services")

    image_providers = initialize_providers(image_providers, services_container)

    logging.info('Downloading requisite data')
    # grab the data for each image_provider.
    # those that can't get their data, we filter out
    return list(filter(ensure_data, image_providers))


def build_images(image_providers, rerender_all=False, threads=1):
    if rerender_all:
        logging.info('Rerendering all images')
    else:
        logging.info('Rendering images')

    if threads == 1:
        for prov in image_providers:
            build_image(prov, rerender_all)
    else:
        with PoolExecutor(threads) as exe:
            exe.map(
                lambda prov: build_image(prov, rerender_all),
                image_providers
            )

    logging.info('Done.')


def build_image(prov, rerender_all):
    output_filename = join(
        OUTPUT,
        dir_for_thing(prov),
        '{}.png'.format(prov.__module__.split('.')[-1])
    )
    if exists(output_filename):
        if not rerender_all:
            return

        move_old(output_filename)

    try:
        logging.info('Building graph for %s', get_name(prov))
        fig = prov.build_image()
        logging.info('Rendering %s', get_name(prov))
        try:
            fig.savefig(output_filename)
        except AttributeError:
            fig.figure.savefig(output_filename)
        plt.close('all')  # don't allow an old image to affect a new one

        if exists(output_filename):
            logging.info('Render successful')
        else:
            logging.info('Render unsuccessful')

    except BdbQuit:
        raise

    except NotImplementedError:
        logging.exception("Can't render %s", get_name(prov))

    except ShapeFileNotFoundException:
        logging.info(
            "Can't render %s; couldn't access required data",
            get_name(prov)
        )

    del prov  # force cleanup


def valid_thread_num(value):
    ivalue = int(value)
    if ivalue < 1:
        raise argparse.ArgumentTypeError("%s is not greater than one" % value)
    return ivalue


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
    parser.add_argument(
        '-d', '--download_data',
        action='store_true',
        help='Just download all the required data'
    )
    parser.add_argument(
        '-t', '--threads',
        action='store',
        default=1,
        type=valid_thread_num,
        help='Number of image rendering threads'
    )
    return parser.parse_args()


def main():
    args = get_args()

    if args.list:
        image_providers = load_image_providers(args.filter)
        for ip in image_providers:
            logging.info(' * %s', get_name(ip))

    elif args.download_data:
        logging.info('Will only download data')
        setup(args)

    else:
        image_providers = setup(args)
        build_images(image_providers, args.rerender, args.threads)


if __name__ == '__main__':
    main()
