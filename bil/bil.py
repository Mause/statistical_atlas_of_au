import time
from glob import iglob
from os.path import splitext, dirname, basename, exists, join
import struct

from PIL import Image
import numpy as np

base = (
    'D:\\stats_data\\cache\\saau\\sections\\'
    'geology\\48006_shp\\globalmap2001\\Raster\\elevation\\'
    'elscnf'
)


def try_parse(v):
    for func in [int, float]:
        try:
            return func(v)
        except ValueError:
            pass
    return v


def parse_header(filename):
    with open(filename + '.hdr') as fh:
        props = map(str.split, fh.read().splitlines())
        return {
            k.upper(): try_parse(v)
            for k, v in props
        }


def format_string(endian, items, nbytes):
    byte = {
        1: 'B',
        2: 'h',
        # 2: 'H',
        # 4: 'f',
        # 4: 'i',
        # 4: 'I',
        # 4: 'l',
        # 4: 'L',
        # 8: 'd',
        # 8: 'q',
        # 8: 'Q',
    }[nbytes]

    return struct.Struct('{}{}{}'.format(endian, items, byte))


def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def transpose(data):
    return list(map(list, zip(*data)))


def parse_row(fh, fmt, ncols, row_data_length):
    data = fh.read(row_data_length)
    items = fmt.unpack(data)
    items = chunks(items, ncols)
    return transpose(items)


def parse_bil(base):
    props = parse_header(base)
    nbytes = props['NBITS'] // 8
    assert 'BANDGAPBYTES' not in props or props['BANDGAPBYTES'] == 0

    endian = '<' if props['BYTEORDER'] == 'I' else '>'

    with open(base + '.bil', 'rb') as fh:
        if 'SKIPBYTES' in props:
            fh.read(props['SKIPBYTES'])

        fmt = format_string(
            endian,
            props['NCOLS'] * props['NBANDS'],
            nbytes
        )
        row_data_length = props['NCOLS'] * props['NBANDS'] * nbytes
        if 'BANDROWBYTES' in props:
            assert row_data_length == props['BANDROWBYTES']

        rows = [
            parse_row(
                fh,
                fmt,
                props['NCOLS'],
                row_data_length
            )
            for row in range(props['NROWS'])
        ]

    return props, np.array(rows)


def parse_points(base, use_c=False):
    from test_bil import timer
    from ffi import c_parse_bil

    if not use_c:
        props, rows = timer(parse_bil)(base)
        points = np.array(rows, dtype=int)
        points = np.array(
            [
                [x, y, points[x][y][0]]
                for y in range(props['NCOLS'])
                for x in range(props['NROWS'])
            ]
        )

    else:
        props, rows = timer(c_parse_bil)(base)
        points = np.array(
            [
                (x, y, bands[0])
                for x, y, bands in rows
            ],
            dtype=int
        )

    points[::, 0] += props['ULXMAP']
    points[::, 1] += props['ULYMAP']

    return points


def try_individual_files():
    path = join(dirname(base), '*.bil')
    paths = list(iglob(path))
    print(len(paths))

    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(20) as exe:
        exe.map(try_individual, paths)


def timer(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        val = func(*args, **kwargs)
        print(func, time.time() - start)
        return val
    return wrapper


@timer
def try_individual(bil):
    name = splitext(bil)[0]

    filename = 'output\\image_{}.png'.format(basename(name))
    if exists(filename):
        return

    pts = np.array([
        [
            point[0]
            for point in row
        ]
        for row in parse_bil(name)
    ])

    shape = (pts[::, 0].max() + 1, pts[::, 1].max() + 1)
    pixels = np.zeros(shape)
    pixels[pts[::, 0], pts[::, 1]] = pts[::, 2]

    Image.fromarray(np.uint8(pixels)).save(filename)


if __name__ == '__main__':
    try_individual_files()
