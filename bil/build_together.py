import re
from glob import glob
from itertools import chain
from os.path import exists

locations = [
    ['vffa', 'vfla', 'wfaa', 'wffa', 'wfla', 'xfaa', 'xffa', 'xfla',   None],
    ['vefl', 'vell', 'weal', 'wefl', 'well', 'xeal', 'xefl', 'xell', 'yeal'],
    ['veff', 'velf', 'weaf', 'weff', 'welf', 'xeaf', 'xeff', 'xelf', 'yeaf'],
    ['vefa', 'vela', 'weaa', 'wefa', 'wela', 'xeaa', 'xefa', 'xela', 'yeaa'],
    ['vdfl', 'vdll', 'wdal', 'wdfl', 'wdll', 'xdal', 'xdfl', 'xdll', 'ydal'],
    ['vdff', 'wdlf', 'wdaf', 'wdff', 'wdlf', 'xdaf', 'xdff', 'xdlf', 'ydaf'],
    [ None,  None,    None,    None,   None,  None,  'xdda', 'xdka',  None]
    [ None,  None,    None,    None,   None,  None,  'xcdl', 'xckl',  None]
]

for location in chain.from_iterable(locations):
    if location:
        assert exists('output/image_el{}.png'.format(location)), location


def transpose(data):
    return list(map(list, zip(*data)))


def resolve(images):
    return [
        [
            images
            for cube in row
        ]
        for row in locations
    ]


def axes(resolved):
    ...


def main():
    images = {}
    for image in glob('output\\*.png'):
        images[re.findall(r'_el(.*).png', image)[0]] = image

    from PIL import Image
    images = {
        name: Image.open(filename)
        for name, filename in images.items()
    }

    blank_image = Image.new(
        "RGB",
        (600 * len(locations[0]), 600 * len(locations))
    )

    resolved = resolve(images)
    width, height = 0, 0

    x, y = 0, 0
    for row in resolved:
        for cube in row:
            if cube:
                print(cube, (x, y))
                blank_image.paste(
                    cube,
                    (x, y)
                )
            x += 600
        x = 0
        y += 600

    blank_image.save('combined.png')

    for im in images.values():
        im.close()

if __name__ == '__main__':
    main()
