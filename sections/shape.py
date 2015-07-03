import os
import logging
import zipfile
from os.path import splitext, join, basename, dirname, exists, isdir
import cartopy.io.shapereader as shpreader


def listdir_r(path):
    for root, _, filenames in os.walk(path):
        for filename in filenames:
            yield join(root, filename)


class ShapeFileNotFoundException(Exception):
    pass


def shape_from_zip(zip_filename, shape_filename=None):
    """
    Loads a shapefile from a zipfile.
    If shape_filename is None, we guess which shape file you want.
    """

    container = dirname(zip_filename)

    dest = join(container, splitext(basename(zip_filename))[0])

    if not (exists(dest) and isdir(dest) and os.listdir(dest)):
        logging.info("%s not yet extracted, extracting...", zip_filename)
        os.makedirs(dest, exist_ok=True)

        with zipfile.ZipFile(zip_filename) as zipper:
            zipper.extractall(dest)

    if shape_filename is None:
        shape_filenames = [
            splitext(filename)[0]
            for filename in listdir_r(dest)
            if splitext(filename)[1] == '.shp'
        ]
        if not shape_filenames:
            msg = "Couldn't find a .shp file in {}".format(zip_filename)

            if splitext(os.listdir(dest)[0])[1] == '.gdb':
                msg += '. Looks like a geodatabase instead.'

            raise ShapeFileNotFoundException(msg)
        shape_filename = shape_filenames[0]

    return shpreader.Reader(join(dest, shape_filename))
