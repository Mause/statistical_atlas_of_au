import struct
import enum
from itertools import count
from collections import namedtuple
from os.path import join

# BASE = 'D:\\stats_data\\luav4g9abl07811a07egfalb132\\prob\\p05v4_25'
BASE = 'D:\\stats_data\\luav4g9abl07811a02egigeo___\\luav4g9abll07811a02egigeo___\\lu05v4ag'

DblBnb = namedtuple('DblBnb', 'llx,lly,urx,ury')
RasterStats = namedtuple('RasterStats', 'min,max,mean,stddev')
TileIndexEntry = namedtuple('TileIndexEntry', 'offset,size')
Header = namedtuple(
    'Header',
    'assorted1,HCellType,CompFlag,assorted2,HPixelSizeX,HPixelSizeY,'
    'XRef,YRef,HTilesPerRow,HTilesPerColumn,HTileXSize,Unknown,HTileYSize'
)

DBLBND_FORMAT = RASTERSTATS_FORMAT = struct.Struct('>4d')
HEADER_FORMAT = struct.Struct(
    '>'
    '8s'  # 8           assorted data, I don't know the purpose.
    'i'  # 4   MSB Int32   HCellType   1 = int cover, 2 = float cover.
    'i'  # 4   MSB Int32   CompFlag    0 = compressed, 1 = uncompressed
    '232s'  # 232         assorted data, I don't know the purpose.
    'd'  # 8   MSB Double  HPixelSizeX Width of a pixel in georeferenced coordinates. Generally 1.0 for ungeoreferenced rasters.
    'd'  # 8   MSB Double  HPixelSizeY Height of a pixel in georeferenced coordinates. Generally 1.0 for ungeoreferenced rasters.
    'd'  # 8   MSB Double  XRef    dfLLX-(nBlocksPerRow*nBlockXSize*dfCellSizeX)/2.0
    'd'  # 8   MSB Double  YRef    dfURY-(3*nBlocksPerColumn*nBlockYSize*dfCellSizeY)/2.0
    'i'  # 4   MSB Int32   HTilesPerRow    The width of the file in tiles (often 8 for files of less than 2K in width).
    'i'  # 4   MSB Int32   HTilesPerColumn The height of the file in tiles. Note this may be much more than the number of tiles actually represented in the index file.
    'i'  # 4   MSB Int32   HTileXSize  The width of a file in pixels. Normally 256.
    'i'  # 4   MSB Int32       Unknown, usually 1.
    'i'  # 4   MSB Int32   HTileYSize  Height of a tile in pixels, usually 4.
)


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
    rmin = fh.read(min_size)

    if min_size == 2:
        fmt = 'h'

    elif min_size == 4:
        fmt = 'i'

    elif min_size == 8:
        fmt = 'q'

    else:
        raise Exception("Invalid min_size: {}".format(min_size))

    return min_size, struct.unpack('>' + fmt, rmin)[0]


def parse_raster_data(filename, tile_index, bounding, header):
    # pixels = (bounding.urx - bounding.lrx) / header.HPixelSizeX
    # lines = (bounding.ury - bounding.lry) / header.HPixelSizeY

    with open(filename, 'rb') as fh:
        check_header(fh)

        for tile_offset, RTileSize in tile_index:
            fh.seek(tile_offset)
            dat = fh.read(2)
            assert dat != b''
            read_size = struct.unpack('>h', dat)[0]
            assert RTileSize == read_size
            if read_size == 0:
                continue
            RTileType = TileType(ord(fh.read(1)))
            RMinSize, RMin = get_min(fh)

            tile_data_length = RTileSize * 2 - 3 - RMinSize

            yield {
                'tile_type': RTileType,
                'tile_data': parse_tile_data(
                    fh.read(tile_data_length)
                )
            }


def parse_tile_data(data):
    None


def parse_raster_statistics(filename):
    with open(filename, 'rb') as fh:
        return RasterStats(*RASTERSTATS_FORMAT.unpack(fh.read()))


def parse_header(filename):
    with open(filename, 'rb') as fh:
        assert struct.unpack('8s', fh.read(8))[0] == b'GRID1.2\x00'
        header = Header(*HEADER_FORMAT.unpack(fh.read()))

        return header._replace(
            HCellType=CellType(header.HCellType),
            CompFlag=CompFlag(header.CompFlag)
        )


def main():
    header = parse_header(join(BASE, 'hdr.adf'))

    bounds = parse_georef_bounds(join(BASE, 'dblbnd.adf'))
    print(bounds)
    print(parse_raster_statistics(join(BASE, 'sta.adf')))

    tile_index = parse_tile_index(join(BASE, 'w001001x.adf'))

    tile_index = list(tile_index)

    path = join(BASE, 'w001001.adf')
    import ipdb
    ipdb.set_trace()
    list(parse_raster_data(path, tile_index, bounds, header))



if __name__ == '__main__':
    main()
