import json
import struct
from glob import iglob
from os.path import splitext, dirname, basename

import numpy as np
# from matplotlib.cm import get_cmap
from matplotlib.colors import Normalize
# import matplotlib.pyplot as plt

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


def parse_points(base):
    props, rows = parse_bil(base)

    points = np.array(
        [
            [x, y, rows[x][y][0]]
            for y in range(props['NCOLS'])
            for x in range(props['NROWS'])
        ]
    )

    points[::, 0] += props['ULXMAP']
    points[::, 1] += props['ULYMAP']

    return points


def get_points():
    path = dirname(base) + '\\*.bil'
    paths = list(iglob(path))
    print(len(paths), 'bils')
    for idx, bil in enumerate(paths[:5], 1):
        pts = parse_points(splitext(bil)[0])
        print(idx, '\t->', basename(bil), '\t->', len(pts))
        yield from pts


def reseat(nums):
    '''
    Moves all contained items such that the small item in the collection aligns
    with zero
    '''

    mini = min(nums)

    if mini > 0:
        nums -= mini
    elif mini < 0:
        nums += abs(mini)

    return nums


def main():
    from PIL import Image

    points = cached_get_points()
    print(len(points))

    import pandas
    keys = ('x', 'y', 'c')
    points = pandas.DataFrame([
        dict(zip(keys, values))
        for values in points
    ])

    points = points[points.c != 61912]

    from collections import Counter
    c = Counter(points.c)
    print('\n'.join(map(str, c.most_common(20))))

    size = (
        int(points.x.max() * 1.25),
        int(points.y.max() * 1.25)
    )
    print('size:', size)
    img = Image.new('P', size)

    vmin = points.c.min()
    vmax = points.c.max()
    norm = Normalize(vmin=vmin, vmax=vmax)

    points.x = reseat(points.x)
    points.y = reseat(points.y)
    points.c = (norm(points.c) * 256).astype(int)

    # img.putdata(pixels)

    for _, point in points.iterrows():
        try:
            img.putpixel((point.x, point.y), point.c)
        except IndexError:
            print(point)
            raise

    img.save('image.png')


def run_test():
    print(parse_bil('sample'))


if __name__ == '__main__':
    run_test()
    # main()
