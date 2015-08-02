import re
from os import walk, makedirs, listdir, unlink
from shutil import copyfile
from os.path import join, basename, dirname
from .__main__ import OUTPUT


FILENAME_RE = re.compile(r'[A-Za-z_]+\.png')


def get_filenames():
    filenames = (
        join(dirpath, filename)
        for dirpath, _, filenames in list(walk(OUTPUT))
        for filename in filenames
    )

    yield from (
        filename
        for filename in filenames
        if 'old' not in filename and FILENAME_RE.match(basename(filename))
    )


def main():
    collated = join(dirname(OUTPUT), 'collated')

    for filename in listdir(collated):
        unlink(join(collated, filename))

    makedirs(collated, exist_ok=True)

    for src in get_filenames():
        dest = join(collated, basename(src))
        print(src, '->', dest)
        copyfile(src, dest)

if __name__ == '__main__':
    main()
