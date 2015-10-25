import time
from glob import iglob
from itertools import chain
from os.path import splitext, dirname, basename, join

from PIL import Image
import numpy as np

base = (
    'D:\\stats_data\\cache\\saau\\sections\\'
    'geology\\48006_shp\\globalmap2001\\Raster\\elevation\\'
    'elscnf'
)
locations = [
    ['vffa', 'vfla', 'wfaa', 'wffa', 'wfla', 'xfaa', 'xffa', 'xfla',   None],
    ['vefl', 'vell', 'weal', 'wefl', 'well', 'xeal', 'xefl', 'xell', 'yeal'],
    ['veff', 'velf', 'weaf', 'weff', 'welf', 'xeaf', 'xeff', 'xelf', 'yeaf'],
    ['vefa', 'vela', 'weaa', 'wefa', 'wela', 'xeaa', 'xefa', 'xela', 'yeaa'],
    ['vdfl', 'vdll', 'wdal', 'wdfl', 'wdll', 'xdal', 'xdfl', 'xdll', 'ydal'],
    ['vdff', 'wdlf', 'wdaf', 'wdff', 'wdlf', 'xdaf', 'xdff', 'xdlf', 'ydaf'],
    [ None,  None,    None,    None,   None,  None,  'xdda', 'xdka',  None],
    [ None,  None,    None,    None,   None,  None,  'xcdl', 'xckl',  None]
]


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        val = func(*args, **kwargs)
        print(func.__name__, time.time() - start)
        return val
    return wrapper


# @timer
def parse_bil(base):
    import rasterio
    with rasterio.drivers():
        bil = rasterio.open(base + '.bil')
        return bil.meta, bil.read()[0]


# @timer
def try_individual_files():
    path = join(dirname(base), '*.bil')

    return map(try_individual, iglob(path))


def try_individual(bil):
    name = splitext(bil)[0]

    props, pixels = parse_bil(name)

    return basename(name), Image.fromarray(np.uint8(pixels))


def transpose(data):
    return list(map(list, zip(*data)))


def resolve(images):
    return [
        [
            images[cube] if cube else None
            for cube in row
        ]
        for row in locations
    ]


def axes(resolved):
    ...


@timer
def read_in():
    images = dict(try_individual_files())
    images = {name[2:]: image for name, image in images.items()}
    return resolve(images)


@timer
def combine(resolved):
    blank_image = Image.new(
        "RGB",
        (600 * len(locations[0]), 600 * len(locations))
    )

    x, y = 0, 0
    for row in resolved:
        for cube in row:
            if cube:
                blank_image.paste(
                    cube,
                    (x, y)
                )
            else:
                x += 600
        x = 0
        y += 600

    return blank_image


@timer
def save(im, filename):
    im.save(filename)


def main():
    resolved = read_in()
    width, height = 0, 0

    save(combine(resolved), 'combined.png')

    for im in chain.from_iterable(resolved):
        if im:
            im.close()

if __name__ == '__main__':
    main()
