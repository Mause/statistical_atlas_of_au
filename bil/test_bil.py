import unittest
from bil import parse_bil


class TestBIL(unittest.TestCase):
    def test_sample(self):
        header, data = parse_bil('sample')

        self.assertEqual(
            header,
            {
                'BYTEORDER': 'I',
                'NBITS': 8,
                'NROWS': 8,
                'NBANDS': 3,
                'NCOLS': 8
            }
        )

        # print(datavalue)

        self.assertEqual(
            data,
            [
                [
                    [0, 0, 255],
                    [0, 0, 255],
                    [0, 64, 255],
                    [0, 64, 255],
                    [0, 128, 255],
                    [0, 128, 255],
                    [0, 255, 255],
                    [0, 255, 255]
                ],
                [
                    [0, 0, 255],
                    [0, 0, 255],
                    [0, 64, 255],
                    [0, 64, 255],
                    [0, 128, 255],
                    [0, 128, 255],
                    [0, 255, 255],
                    [0, 255, 255]
                ],
                [
                    [64, 0, 128],
                    [64, 0, 128],
                    [64, 64, 128],
                    [64, 64, 128],
                    [64, 128, 128],
                    [64, 128, 128],
                    [64, 255, 128],
                    [64, 255, 128]
                ],
                [
                    [64, 0, 128],
                    [64, 0, 128],
                    [64, 64, 128],
                    [64, 64, 128],
                    [64, 128, 128],
                    [64, 128, 128],
                    [64, 255, 128],
                    [64, 255, 128]
                ],
                [
                    [128, 0, 64],
                    [128, 0, 64],
                    [128, 64, 64],
                    [128, 64, 64],
                    [128, 128, 64],
                    [128, 128, 64],
                    [128, 255, 64],
                    [128, 255, 64]
                ],
                [
                    [128, 0, 64],
                    [128, 0, 64],
                    [128, 64, 64],
                    [128, 64, 64],
                    [128, 128, 64],
                    [128, 128, 64],
                    [128, 255, 64],
                    [128, 255, 64]
                ],
                [
                    [255, 0, 0],
                    [255, 0, 0],
                    [255, 64, 0],
                    [255, 64, 0],
                    [255, 128, 0],
                    [255, 128, 0],
                    [255, 255, 0],
                    [255, 255, 0]
                ],
                [
                    [255, 0, 0],
                    [255, 0, 0],
                    [255, 64, 0],
                    [255, 64, 0],
                    [255, 128, 0],
                    [255, 128, 0],
                    [255, 255, 0],
                    [255, 255, 0]
                ]
            ]
        )


def rgb_to_hex(rgb):
    t = lambda q: hex(q)[2:].ljust(2, '0')
    return '#{}{}{}'.format(*map(t, rgb))


def do_test():
    header, data = parse_bil('sample')
    import numpy as np
    import matplotlib.pyplot as plt

    from pprint import pprint
    # pprint(data)

    points = np.array([
        [y, x, rgb_to_hex(data[x][y])]
        for x in range(8)
        for y in range(8)
    ])

    plt.scatter(
        x=points[::, 0],
        y=points[::, 1],
        color=points[::, 2],
    )

    plt.show()


if __name__ == '__main__':
    unittest.main()
    # do_test()
