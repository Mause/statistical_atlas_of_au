"""
https://web.archive.org/web/20121124091208/
http://home.gdal.org/projects/aigrid/aigrid_format.html
"""

import struct
import enum
from collections import namedtuple
from os.path import join

# BASE = 'D:\\stats_data\\luav4g9abl07811a07egfalb132\\prob\\p05v4_25'
BASE = (
    'D:\\stats_data\\luav4g9abl07811a02egigeo___\\'
    'luav4g9abll07811a02egigeo___\\lu05v4ag'
)

DblBnb = namedtuple('DblBnb', 'llx,lly,urx,ury')
RasterStats = namedtuple('RasterStats', 'min,max,mean,stddev')
TileIndexEntry = namedtuple('TileIndexEntry', 'offset,size')
Header = namedtuple(
    'Header',
    'HCellType,CompFlag,HPixelSizeX,HPixelSizeY,'
    'XRef,YRef,HTilesPerRow,HTilesPerColumn,HTileXSize,HTileYSize'
)

DBLBND_FORMAT = RASTERSTATS_FORMAT = struct.Struct('>4d')
HEADER_FORMAT = struct.Struct('>8xii232xddddiii4xi')

MAGICS = {
    b'\x00\x00\x27\x0A\xFF\xFF\xFC\x14',
    b'\x00\x00\x27\x0A\xFF\xFF\xFB\xF8'
}


def unpack(fh, fmt, length):
    checking = fmt.format if isinstance(fmt, struct.Struct) else fmt
    assert checking[0] in {'>', b'>'}

    buff = fh.read(length)
    assert len(buff) == length, (buff, length)
    return struct.unpack(fmt, buff)


class CellType(enum.Enum):
    IntCover = 1
    FloatCover = 2


class CompFlag(enum.Enum):
    Compressed = 0
    Uncompressed = 1


class TileType(enum.Enum):
    ConstantBlock = 0x00  # (constant block)
    # All pixels take the value of the RMin. Data is ignored. It appears there
    # is sometimes a bit of meaningless data (up to four bytes) in the block.

    Raw1BitData = 0x01  # (raw 1bit data)
    # One full tile worth of data pixel values follows the RMin field, with
    # 1bit per pixel.

    Raw4BitData = 0x04  # (raw 4bit data)
    # One full tiles worth of data pixel values follows the RMin field, with 4
    # bits per pixel. The high order four bits of a byte comes before the low
    # order four bits.

    RawByteData = 0x08  # (raw byte data)
    # One full tiles worth of data pixel values (one byte per pixel) follows
    # the RMin field.

    Raw16BitData = 0x10  # (raw 16bit data)
    # One full tiles worth of data pixel values follows the RMin field, with 16
    # bits per pixel (MSB).

    Raw32BitData = 0x20  # (raw 32bit data)
    # One full tiles worth of data pixel values follows the RMin field, with 32
    # bits per pixel (MSB).

    Literal16Bit = 0xCF  # (16 bit literal runs/nodata runs)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as:
    # Marker < 128: The marker is followed by Marker pixels of literal data
    # with two MSB bytes per pixel.
    # Marker > 127: The marker indicates that 256-Marker pixels of no data
    # pixels should be put into the output stream. No data (other than the next
    # marker) follows this marker.

    LiteralNoDataRuns = 0xD7  # (literal runs/nodata runs)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as:
    # Marker < 128: The marker is followed by Marker pixels of literal data
    # with one byte per pixel.
    # Marker > 127: The marker indicates that 256-Marker pixels of no data
    # pixels should be put into the output stream. No data (other than the next
    # marker) follows this marker.

    RMinNoDataRuns = 0xDF  # (RMin runs/nodata runs)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as:
    # Marker < 128: The marker is followed by Marker pixels of literal data
    # with one byte per pixel.
    # Marker > 127: The marker indicates that 256-Marker pixels of no data
    # pixels should be put into the output stream. No data (other than the next
    # marker) follows this marker.
    # This is similar to 0xD7, except that the data size is zero bytes instead
    # of 1, so only RMin values are inserted into the output stream.

    RunLengthEncoded32bit = 0xE0  # (run length encoded 32bit)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as a count. The four bytes following the
    # count should be interpreted as an MSB Int32 value. They indicate that
    # count pixels of value should be inserted into the output stream.

    RunLengthEncoded16bit = 0xF0  # (run length encoded 16bit)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as a count. The two bytes following the count
    # should be interpreted as an MSB Int16 value. They indicate that count
    # pixels of value should be inserted into the output stream.

    RunLengthEncoded8bit0 = 0xFC
    RunLengthEncoded8bit1 = 0xF8  # (run length encoded 8bit)
    # The data is organized in a series of runs. Each run starts with a marker
    # which should be interpreted as a count. The following byte is the value.
    # They indicate that count pixels of value should be inserted into the
    # output stream. The intepretation is the same for 0xFC, and 0xF8. I
    # believe that 0xFC has a lower dynamic (2 bit) range than 0xF8
    # (4 or 8 bit).

    RMinCCITTRLE1Bit = 0xFF  # (RMin CCITT RLE 1Bit)
    # The data stream for this file is CCITT RLE (G1 fax) compressed. The
    # format is complex but source is provided with the sample program (derived
    # from libtiff) for reading it. The result of uncompressing is 1bit data so
    # which the RMin value should be added.


def check_header(fh):
    assert fh.read(8) in MAGICS
    assert fh.read(16) == (b'\x00' * 16)

    file_size = unpack(fh, '>i', 4)[0]  # file size in shorts
    assert file_size > 0

    assert fh.read(72) == (b'\x00' * 72)

    assert fh.tell() == 100

    return file_size


def parse_georef_bounds(filename):
    "dblbnd.adf"
    with open(filename, 'rb') as fh:
        return DblBnb(*DBLBND_FORMAT.unpack(fh.read()))


def parse_tile_index(filename):
    with open(filename, 'rb') as fh:
        file_size = check_header(fh)

        file_bytes = file_size * 2
        data_bytes = file_bytes - 100

        entries = data_bytes // 8

        yield from (
            TileIndexEntry(*unpack(fh, '>ii', 8))
            for _ in range(entries)
        )

        assert fh.read() == b''  # sanity check


def get_min(fh):
    min_size = ord(fh.read(1))

    assert min_size in {2, 4, 8}, min_size

    fmt = {
        2: 'h',
        4: 'i',
        8: 'q'
    }[min_size]

    return min_size, struct.unpack(fmt, fh.read(min_size))[0]


def parse_raster_data(filename, tile_index, bounding, header):
    lrx = bounding.llx
    lry = bounding.lly
    pixels = (bounding.urx - lrx) / header.HPixelSizeX
    lines = (bounding.ury - lry) / header.HPixelSizeY

    with open(filename, 'rb') as fh:
        check_header(fh)

        for tile_offset, RTileSize in sorted(tile_index):
            fh.seek(100 + tile_offset)
            read_size = unpack(fh, '>h', 2)[0]
            if read_size == 0:
                continue

            RTileType = TileType(ord(fh.read(1)))
            RMinSize, RMin = get_min(fh)

            tile_data_length = RTileSize * 2 - 3 - RMinSize

            yield {
                'tile_type': RTileType,
                'tile_data': parse_tile_data(
                    fh.read(tile_data_length),
                    RMin,
                    RTileType
                )
            }


def parse_tile_data(*args):
    print(args)


def parse_raster_statistics(filename):
    with open(filename, 'rb') as fh:
        return RasterStats(*RASTERSTATS_FORMAT.unpack(fh.read()))


def parse_header(filename):
    with open(filename, 'rb') as fh:
        assert unpack(fh, '>8s', 8)[0] == b'GRID1.2\x00'
        header = Header(*HEADER_FORMAT.unpack(fh.read()))

        return header._replace(
            HCellType=CellType(header.HCellType),
            CompFlag=CompFlag(header.CompFlag)
        )


class Adf:
    def __init__(self, directory):
        self.directory = directory

    @property
    def header(self):
        if not hasattr(self, '_header'):
            self._header = parse_header(join(self.directory, 'hdr.adf'))

        return self._header

    @property
    def bounds(self):
        if not hasattr(self, '_bounds'):
            self._bounds = parse_georef_bounds(join(BASE, 'dblbnd.adf'))

        return self._bounds

    @property
    def stats(self):
        if not hasattr(self, '_stats'):
            self._stats = parse_raster_statistics(
                join(self.directory, 'sta.adf')
            )

        return self._stats

    @property
    def _tile_index(self):
        if not hasattr(self, '__tile_index'):
            self.__tile_index = list(
                parse_tile_index(join(self.directory, 'w001001x.adf'))
            )

        return self.__tile_index

    @property
    def raster_data(self):
        if not hasattr(self, '_raster_data'):
            path = join(self.directory, 'w001001.adf')
            self._raster_data = list(parse_raster_data(
                path, self._tile_index, self.bounds, self.header
            ))

        return self._raster_data


def main():
    adf = Adf(BASE)

    print(adf.header)
    print(adf.bounds)
    print(adf.stats)

    adf._tile_index

    print(adf.raster_data)


if __name__ == '__main__':
    main()
