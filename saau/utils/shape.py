import os
from os.path import splitext, join
import cartopy.io.shapereader as shpreader

from . import unzip


def listdir_r(path):
    'Recursive listdir'
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

    dest = unzip(zip_filename)

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
