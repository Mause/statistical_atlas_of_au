import re
import json
import struct
import ctypes
from queue import Queue
from functools import lru_cache
from collections import namedtuple, OrderedDict

base = (
    'D:\\stats_data\\cache\\saau\\sections\\'
    'geology\\48006_shp\\globalmap2001\\Raster\\elevation\\'
    'elscnf'
)
NUM_RE = re.compile(r'(\d*)')
STR_RE = re.compile(r'([A-Za-z0-9_ -]*)')
PUNC = set('{},:*')


FORMATS = json.load(open('formats.json'))


class IMGFile(namedtuple('IMGFile', 'version,rootEntry,mifDictionary')):

    def __hash__(self):
        return hash(
            (
                self.rootEntry,
                self.mifDictionary
            )
        )

    def __eq__(self, other):
        return hash(self) == hash(other)


MIF_DATA_TYPES = {
    '1': 1,
    '2': 1,
    '4': 1,
    'C': 1,
    'c': 1,
    'e': 1,
    'S': 2,
    's': 2,
    't': 4,
    'L': 4,
    'l': 4,
    'i': 4,
    'f': 4,
    'd': 8,
    'm': 8,
    'M': 16,
    'b': 'dynamic',
    'o': 'dynamic',
    'x': 'dynamic'
}


class BadFormatString(Exception):
    pass


def nc(tokens):
    name = tokens.pop(0)
    comma = tokens.pop(0)
    assert comma == ','
    return name


def parse_to_struct(tokens):
    while tokens:
        token = tokens.pop(0)
        if token == '{':
            block = list(parse_to_struct(tokens))
            name = nc(tokens)

            yield (name, block)

        elif token == '}':
            return

        elif isinstance(token, int):
            length = token
            assert tokens.pop(0) == ':'
            name = tokens.pop(0)
            comma = tokens.pop(0)

            typ = determine_type(name)

            if typ in {'*', 'p'}:
                meta = typ
                typ = name[1:2]
                name = name[1:]
            else:
                meta = None

            if typ == 'o':
                # okay, custom type
                type_name = name[1:]

                if type_name == 'Emif_String':
                    typ = '16c'
                else:
                    raise Exception

                yield (1, {'type': typ, 'name': nc(tokens), 'meta': meta})

            elif typ == 'e':
                # okay, enum

                n_elems = int(name[1:])
                yield (
                    length,
                    {
                        "type": "c",
                        "values": [nc(tokens) for _ in range(n_elems)],
                        "name": nc(tokens),
                        'meta': meta
                    }
                )

            else:
                assert comma == ','

                yield (length, {'type': typ, 'name': name[1:], 'meta': meta})

        else:
            raise BadFormatString(token)


class Entry:

    def __init__(self, ptr, next, prev, parent, child, data, dataSize, name,
                 typ, modTime):
        self.ptr = ptr  # essentially a unique identifier within the file
        self.next = next
        self.prev = prev
        self.parent = parent
        self.child = child
        self.data = data
        self.dataSize = dataSize
        self.name = name
        self.typ = typ
        self.modTime = modTime

    def __hash__(self):
        return hash(self.ptr)

    def __eq__(self, other):
        return hash(self) == hash(other)

    __str__ = __repr__ = lambda self: '<Entry {} of type {}>'.format(
        self.name, self.typ
    )


def clean_string(string):
    return ctypes.create_string_buffer(b''.join(string)).value.decode()


class EntryParser:

    def __init__(self, fh, root_ptr):
        self.fh = fh
        self.root_ptr = root_ptr
        self.queue = Queue()
        self.seen = {}

    def parse(self):
        root = type('', (), {'child': None})()
        self.queue.put((root, 'child', self.root_ptr))
        while not self.queue.empty():
            dest, name, ptr = self.queue.get()
            setattr(dest, name, self.parse_entry(ptr, dest))
            if name == 'child':
                setattr(
                    getattr(dest, name),
                    'parent',
                    dest
                )
        root.child.parent = None
        return root.child

    def parse_data(self, typ, ptr):
        if typ == 'Eimg_DependentFile':
            __import__('ipdb').set_trace()
        self.fh.seek(ptr)
        data = mif(typ).from_file(self.fh)
        print(typ, end=' ')
        pprint(data)
        return data

    def parse_entry(self, ptr, parent):
        if ptr in self.seen:
            return self.seen[ptr]

        self.fh.seek(ptr)
        raw_entry = mif('Ehfa_Entry').from_file(self.fh)

        raw_entry['name'] = clean_string(raw_entry['name'])
        raw_entry['typ'] = clean_string(raw_entry.pop('type'))

        raw_entry['data'] = (
            self.parse_data(raw_entry['typ'], raw_entry['data'])
            if raw_entry['data'] != 0
            else None
        )

        ent = Entry(ptr, **raw_entry)
        self.seen[ptr] = ent

        self.enqueue(ent, 'next')
        self.enqueue(ent, 'prev')
        self.enqueue(ent, 'child')

        return ent

    def enqueue(self, ent, label):
        if getattr(ent, label):
            self.queue.put((ent, label, getattr(ent, label)))


class MIF(namedtuple('MIF', 'name,struct_def,spec')):
    __str__ = lambda self: '<MIF {}>'.format(self.name)

    def _from_file(self, fh):
        data = self.struct_def.unpack_from(fh.read(self.struct_def.size))

        idx = 0
        for length, spec in self.spec:
            name = spec['name']
            val = data[idx:idx + length]
            if isinstance(val, tuple) and len(val) == 1:
                val = val[0]
            yield name, val
            idx += length

    def from_file(self, fh):
        return dict(self._from_file(fh))


def determine_type(typ):
    return 'L' if typ[0] == 't' else typ[0]


@lru_cache()
def compile_mif(name, definition):
    tokens = list(to_tokens(definition))
    bits = OrderedDict(list(parse_to_struct(tokens)))

    bits = list(bits.values())[0]

    parts = [
        '{}{}'.format(
            '' if length == 1 else length,
            spec['type']
        )
        for length, spec in bits
    ]

    return MIF(
        name,
        struct.Struct('<' + ''.join(parts)),
        bits
    )


def mif(name):
    return compile_mif(name, FORMATS[name])


def parse_mif_dictionary(fh, ptr):
    ...


def parse(filename):
    with open(filename, 'rb') as fh:
        data = mif('Ehfa_HeaderTag').from_file(fh)
        label, ptr = data['label'], data['headerPtr']
        assert clean_string(label) == 'EHFA_HEADER_TAG'

        fh.seek(ptr)

        ehfa_file = mif('Ehfa_File').from_file(fh)
        assert ehfa_file['version'] == 1

        fh.seek(ehfa_file['rootEntryPtr'])

        dictionaryPtr = ehfa_file['dictionaryPtr']
        mif_dictionary = (
            None if dictionaryPtr == 0
            else parse_mif_dictionary(fh, dictionaryPtr)
        )

        root = EntryParser(fh, ehfa_file['rootEntryPtr']).parse()

    return IMGFile(ehfa_file["version"], root, mif_dictionary)


def main():
    print(parse(base + '.aux'))


def to_tokens(string):
    while string:
        if string[0] in PUNC:
            yield string[0]
            string = string[1:]

        elif string[0].isnumeric():
            m = NUM_RE.match(string)

            yield int(m.group())

            string = string[len(m.group()):]

        else:
            m = STR_RE.match(string)

            yield m.group()

            string = string[len(m.group()):]


if __name__ == '__main__':
    main()
