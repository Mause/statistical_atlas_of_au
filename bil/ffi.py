import cffi
import struct

ffi = cffi.FFI()
ffi.cdef('''
typedef struct {
    int NBITS;
    int BYTEORDER;
    int SKIPBYTES;
    int NROWS;
    int NBANDS;
    int NCOLS;
    int BANDGAPBYTES;
    int BANDROWBYTES;
} BILHeader;

// the union type which should be used is specified by the header
typedef struct {
    union {
        signed char eight;
        int sixteen;
    };
} Value;

typedef struct {
    Value**** rows;
    BILHeader* header;
} BIL;

BIL* parse_bil(char* base);
''')

lib = ffi.dlopen('bil.dll')


def c_parse_bil(base):
    return convert_rows(lib.parse_bil(base.encode('ascii')))




def convert_rows(res):
    attr_name = {
        8: 'eight',
        16: 'sixteen'
    }[res.header.NBITS]
    return [
        [
            [
                getattr(res.rows[row][column][band], attr_name)
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
