#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>

typedef struct {
    char BYTEORDER;  // BYTEORDER     I
    char* LAYOUT;     // LAYOUT        BIL
    int NROWS;         // NROWS         8
    int NCOLS;         // NCOLS         6
    int NBANDS;        // NBANDS        1
    int NBITS;         // NBITS         32
    int BANDROWBYTES;   // BANDROWBYTE   24
    int TOTALROWBYTES; // TOTALROWBYTES 24
    int SKIPBYTES;
    int BANDGAPBYTES;  // BANDGAPBYTES  0
    double NODATA;    // NODATA        0
    double ULXMAP;    // ULXMAP        2000.000
    double ULYMAP;    // ULYMAP        3000.000
    double XDIM;      // XDIM          5.000000
    double YDIM;      // YDIM          5.000000
    double SCALE;     // SCALE         100
    double OFFSET;    // OFFSET        100.000000
} BILHeader;

typedef enum {
    BYTEORDER,
    LAYOUT,
    NROWS,
    NCOLS,
    NBANDS,
    NBITS,
    BANDROWBYTES,
    TOTALROWBYTES,
    BANDGAPBYTES,
    NODATA,
    ULXMAP,
    ULYMAP,
    XDIM,
    YDIM,
    SCALE,
    OFFSET,
    SKIPBYTES
} HeaderValue;

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


BIL* make_bil(BILHeader* header) {
    BIL* b;
    int nbytes, row, col, band;
    nbytes = header->NBITS / 8;

    b = malloc(sizeof(*b));
    b->header = header;
    b->rows = malloc(sizeof(Value****) * header->NROWS);
    for (row=0; row<header->NROWS; row++) {
        b->rows[row] = malloc(sizeof(Value***) * header->NCOLS);
        for (col=0; col<header->NCOLS; col++) {
            b->rows[row][col] = malloc(sizeof(Value**) * header->NBANDS);
            for (band=0; band<header->NBANDS; band++) {
                b->rows[row][col][band] = malloc(sizeof(Value));
            }
        }
    }
    if (b->rows[0] == NULL) {
        perror("");
    }

    return b;
}


void white(FILE* fh) {
    char c;
    while ((c = fgetc(fh)) == ' ') {}
    ungetc(c, fh);
}


#define HEADER_NAME(hname, hval) if (strcmp(name, (hname)) == 0) return hval;
int classify(char* name) {
    HEADER_NAME("NBITS", NBITS)
    HEADER_NAME("SKIPBYTES", SKIPBYTES)
    HEADER_NAME("NROWS", NROWS)
    HEADER_NAME("NBANDS", NBANDS)
    HEADER_NAME("NCOLS", NCOLS)
    HEADER_NAME("BANDGAPBYTES", BANDGAPBYTES)
    HEADER_NAME("BANDROWBYTES", BANDROWBYTES)
    HEADER_NAME("TOTALROWBYTES", TOTALROWBYTES)
    HEADER_NAME("BYTEORDER", BYTEORDER)
    HEADER_NAME("LAYOUT", LAYOUT)
    HEADER_NAME("NODATA", NODATA)
    HEADER_NAME("ULXMAP", ULXMAP)
    HEADER_NAME("ULYMAP", ULYMAP)
    HEADER_NAME("XDIM", XDIM)
    HEADER_NAME("YDIM", YDIM)
    HEADER_NAME("SCALE", SCALE)
    HEADER_NAME("OFFSET", OFFSET)
    return -1;
}


void parse_header_val_int(int* dest, FILE* fh) {
    int i = 0;
    assert(fscanf(fh, "%d", &i) == 1);
    *dest = i;
}

void parse_header_val_double(double* dest, FILE* fh) {
    double i = 0;
    assert (fscanf(fh, "%lf", &i) == 1);
    *dest = i;
}

// NROWS         600
// NCOLS         960
// NBANDS        1
// NBITS         16
// BANDROWBYTES        1920
// TOTALROWBYTES       1920
// BANDGAPBYTES         0

// BYTEORDER      M
// LAYOUT       BIL
// NODATA        -9999
// ULXMAP          72.00416666666666
// ULYMAP         -50.00416666666667
// XDIM          0.00833333333333
// YDIM          0.00833333333333

void parse_byte_order(BILHeader* bh, FILE* fh) {
    white(fh);
    bh->BYTEORDER = fgetc(fh);
    printf("BYTEORDER: \"%c\"\n", bh->BYTEORDER);
}


void parse_header_string(char** dest, FILE* fh) {
    *dest = malloc(sizeof(char) * 256);
    white(fh);
    fgets(
        *dest,
        256 * sizeof(char),
        fh
    );
}


void parse_header_val(BILHeader* bh, int ident, FILE* fh) {
    switch (ident) {
        case NBITS:         parse_header_val_int(&(bh->NBITS),         fh); break;
        case SKIPBYTES:     parse_header_val_int(&(bh->SKIPBYTES),     fh); break;
        case NROWS:         parse_header_val_int(&(bh->NROWS),         fh); break;
        case NBANDS:        parse_header_val_int(&(bh->NBANDS),        fh); break;
        case NCOLS:         parse_header_val_int(&(bh->NCOLS),         fh); break;
        case BANDGAPBYTES:  parse_header_val_int(&(bh->BANDGAPBYTES),  fh); break;
        case TOTALROWBYTES: parse_header_val_int(&(bh->TOTALROWBYTES), fh); break;
        case BANDROWBYTES:  parse_header_val_int(&(bh->BANDROWBYTES),  fh); break;
        case NODATA:        parse_header_val_double(&(bh->NODATA),     fh); break;
        case BYTEORDER:     parse_byte_order(bh,                       fh); break;
        case LAYOUT:        parse_header_string(&(bh->LAYOUT),         fh); break;
        case ULXMAP:        parse_header_val_double(&(bh->ULXMAP),     fh); break;
        case ULYMAP:        parse_header_val_double(&(bh->ULYMAP),     fh); break;
        case XDIM:          parse_header_val_double(&(bh->XDIM),       fh); break;
        case YDIM:          parse_header_val_double(&(bh->YDIM),       fh); break;
        case SCALE:         parse_header_val_double(&(bh->SCALE),      fh); break;
        case OFFSET:        parse_header_val_double(&(bh->OFFSET),     fh); break;
        default: assert(0 != 1);
    }
}


BILHeader* parse_header(char* base) {
    FILE* fh;
    char buffer[1024];
    int ident, *ibh;
    BILHeader* bh;
    char *filename;

    filename = strdup(base);
    strcat(filename, ".hdr");

    fh = fopen(filename, "rb");
    if (fh == NULL) return NULL;

    bh = malloc(sizeof(*bh));
    ibh = (int*)bh;

    while (fscanf(fh, "%s", buffer) == 1) {
        ident = classify(buffer);

        if (ident != -1) {
            parse_header_val(bh, ident, fh);
        } else {
            printf("Invalid header name; %s\n", buffer);
            return NULL;
            fgets(buffer, 1024, fh);
        }
    }

    return bh;
}


void parse_to_val(int nbits, char* value, Value* val) {
    switch (nbits) {
        case 8: {
            val->eight = value[0];
            break;
        }
        case 16: {
            val->sixteen = (value[1] << 8) + value[0];
            break;
        }
        default: {
            printf("%db its\n", nbits);
            assert(1 == 0);
        }
    }
}


__declspec(dllexport) BIL* parse_bil(char* base) {
    BILHeader* props;
    int nbytes, row, band, column;
    FILE* fh;
    BIL* b;
    char endian;
    char *filename;
    char buffer[1024];

    props = parse_header(base);
    if (props == NULL) return NULL;

    nbytes = props->NBITS / 8;
    endian = props->BYTEORDER == 'I' ? '<' : '>';

    filename = strcat(base, ".bil");

    fh = fopen(filename, "rb");
    if (fh == NULL) return NULL;

    fread(buffer, sizeof(char), props->SKIPBYTES, fh);

    b = make_bil(props);

    for (row = 0; row < props->NROWS; row++) {
        for (band = 0; band < props->NBANDS; band++) {
            for (column = 0; column < props->NCOLS; column++) {
                char* value = malloc(sizeof(char) * nbytes);
                fread(
                    value,
                    sizeof(char),
                    nbytes,
                    fh
                );
                parse_to_val(
                    props->NBITS,
                    value,
                    b->rows[row][column][band]
                );
                fread(buffer, sizeof(char), props->BANDGAPBYTES, fh);
            }
        }
    }

    return b;
}

int main(int argc, char const *argv[]) {
    BIL* b = parse_bil("sample");
    int row, column, band;

    for (row=0; row<b->header->NROWS; row++) {
        for (column=0; column<b->header->NCOLS; column++) {
            printf(":");
            for (band=0; band<b->header->NBANDS; band++) {
                printf("%x:", b->rows[row][column][band]);
            }
            printf(" ");
        }
        printf("\n");
    }

    /* code */
    return 0;
}
