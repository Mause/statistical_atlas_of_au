import cffi
import struct

ffi = cffi.FFI()
ffi.cdef('''typedef struct {
    int NBITS;
    int BYTEORDER;
    int SKIPBYTES;
    int NROWS;
    int NBANDS;
    int NCOLS;
    int BANDGAPBYTES;
    int BANDROWBYTES;
} BILHeader;

typedef struct {
    char**** rows;
    BILHeader* header;
} BIL;
BIL* parse_bil(char* base);
''')

lib = ffi.dlopen('bil.dll')


def c_parse_bil(base):
    return convert_rows(lib.parse_bil(base.encode('ascii')))


def decode(val):
    return ord(val)
    # return struct.unpack('h', val)[0]


def coallesce(string, nbytes):
    return decode(b''.join(string[i] for i in range(nbytes)))


def convert_rows(res):
    nbytes = res.header.NBITS // 8
    return [
        [
            [
                coallesce(
                    res.rows[row][column][band],
                    nbytes
                )
                for band in range(res.header.NBANDS)
            ]
            for column in range(res.header.NCOLS)
        ]
        for row in range(res.header.NROWS)
    ]


def main():
    from bil import base
    import time

    start = time.time()
    c_parse_bil(base)
    print(time.time() - start)

    globals()['decode'] = lib.decode

    print(decode)


if __name__ == '__main__':
    main()
