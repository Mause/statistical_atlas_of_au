#include <stdlib.h>
#include <stdio.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>

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

typedef struct {
    char**** rows;
    BILHeader* header;
} BIL;


BIL* make_bil(BILHeader* header) {
    BIL* b;
    int nbytes, row, col, band;
    nbytes = header->NBITS / 8;

    b = calloc(sizeof(*b), 1);
    b->header = header;
    b->rows = calloc(sizeof(char****), header->NROWS);
    for (row=0; row<header->NROWS; row++) {
        b->rows[row] = calloc(sizeof(char***), header->NCOLS);
        for (col=0; col<header->NCOLS; col++) {
            b->rows[row][col] = calloc(sizeof(char**), header->NBANDS);
            for (band=0; band<header->NBANDS; band++) {
                b->rows[row][col][band] = calloc(nbytes, sizeof(char));
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
    fputc(c, fh);
}

typedef enum {
    NBITS,
    BYTEORDER,
    SKIPBYTES,
    NROWS,
    NBANDS,
    NCOLS,
    BANDGAPBYTES,
    BANDROWBYTES
} HeaderValue;


size_t classify(char* name) {
    if (strcmp(name, "NBITS") == 0)        return NBITS;
    // if (strcmp(name, "BYTEORDER") == 0)    return BYTEORDER;
    if (strcmp(name, "SKIPBYTES") == 0)    return SKIPBYTES;
    if (strcmp(name, "NROWS") == 0)        return NROWS;
    if (strcmp(name, "NBANDS") == 0)       return NBANDS;
    if (strcmp(name, "NCOLS") == 0)        return NCOLS;
    if (strcmp(name, "BANDGAPBYTES") == 0) return BANDGAPBYTES;
    if (strcmp(name, "BANDROWBYTES") == 0) return BANDROWBYTES;
    return -1;
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
            int i = 0;
            assert(fscanf(fh, "%d", &i) == 1);
            switch (ident) {
                case NBITS:        bh->NBITS = i;        break;
                // case BYTEORDER:    bh->BYTEORDER = i;    break;
                case SKIPBYTES:    bh->SKIPBYTES = i;    break;
                case NROWS:        bh->NROWS = i;        break;
                case NBANDS:       bh->NBANDS = i;       break;
                case NCOLS:        bh->NCOLS = i;        break;
                case BANDGAPBYTES: bh->BANDGAPBYTES = i; break;
                case BANDROWBYTES: bh->BANDROWBYTES = i; break;
                default: assert(0 != 1);
            }
        } else {
            fgets(buffer, 1024, fh);
        }
    }

    return bh;
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
                fread(
                    b->rows[row][column][band],
                    sizeof(char),
                    nbytes,
                    fh
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
