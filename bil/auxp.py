import re
import json
import struct
import ctypes
from queue import Queue
from collections import OrderedDict

base = (
    'D:\\stats_data\\cache\\saau\\sections\\'
    'geology\\48006_shp\\globalmap2001\\Raster\\elevation\\'
    'elscnf'
)
NUM_RE = re.compile(r'(\d*)')
STR_RE = re.compile(r'([A-Za-z0-9_ -]*)')
PUNC = set('{},:')


FORMATS = json.load(open('formats.json'))




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

            if typ == 'o':
                # okay, custom type
                type_name = name[1:]

                if type_name == 'Emif_String':
                    typ = '16c'
                else:
                    raise Exception

                yield (1, {'type': typ, 'name': nc(tokens)})

            elif typ == 'e':
                # okay, enum

                n_elems = int(name[1:])
                yield (
                    length,
                    {
                        "type": "c",
                        "values": [nc(tokens) for _ in range(n_elems)],
                        "name": nc(tokens)
                    }
                )

            else:
                assert comma == ','

                yield (length, {'type': typ, 'name': name[1:]})

        else:
            raise BadFormatString(token)


class Entry:
    def __init__(self, nxt, prev, parent, child, data, dataSize, name, typ,
                 modTime):
        self.nxt = nxt
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
        # return hash((
        #     self.ptr,
        #     self.next,
        #     self.prev,
        #     self.parent,
        #     self.child,
        #     self.data,
        #     self.dataSize,
        #     self.name,
        #     self.typ,
        #     self.modTime
        # ))

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


    def parse_entry(self, ptr, parent):
        if ptr in self.seen:
            return self.seen[ptr]

        self.fh.seek(ptr)

        (
            nxt, prev, _, child, data, dataSize,
            name, typ, modTime
        ) = struct.unpack('IIIIIl64s32sL', self.fh.read(124))

        self.fh.seek(data)
        data = self.fh.read(dataSize)

        name = self.clean_string(name)
        typ = self.clean_string(typ)

        ent = Entry(
            nxt=nxt or None,
            prev=prev or None,
            parent=parent,
            child=child or None,
            data=data,
            dataSize=dataSize,
            name=name,
            typ=typ,
            modTime=modTime,
        )
        self.seen[ptr] = ent

        self.enqueue(ent, 'next')
        self.enqueue(ent, 'prev')
        self.enqueue(ent, 'child')

        return ent

    def enqueue(self, ent, label):
        if getattr(ent, label):
            self.queue.put((ent, label, getattr(ent, label)))





class MIF:
    def __init__(self, struct_def, spec):
        self.struct_def = struct_def
        self.spec = spec

    def _from_file(self, fh):
        data = self.struct_def.unpack_from(fh.read(self.struct_def.size))

        idx = 0
        for length, spec in self.spec:
            name = spec['name']
            val = data[idx:idx+length]
            if isinstance(val, tuple) and len(val) == 1:
                val = val[0]
            yield name, val
            idx += length

    def from_file(self, fh):
        return dict(self._from_file(fh))


def determine_type(typ):
    return 'L' if typ[0] == 't' else typ[0]


def compile_mif(definition):
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
        struct.Struct(''.join(parts)),
        bits
    )


def parse(filename):
    with open(filename, 'rb') as fh:
        label, ptr = struct.unpack('15sxcxxx', fh.read(20))
        label = label.decode()
        ptr = ord(ptr)
        print(label, ptr)

        fh.seek(ptr)

        version = struct.unpack('l', fh.read(4))[0]
        assert version == 1, version

        freeList, rootEntryPtr, entryHeaderLength, dictionaryPtr = (
            struct.unpack('<IIhI', fh.read(14))
        )

        root = EntryParser(fh, rootEntryPtr).parse()
    return root


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
    # from pprint import pprint
    # tokens = list(to_tokens(multiple))
    __import__('ipdb').set_trace()
    # pprint(OrderedDict(list(parse_to_struct(tokens))))
    main()
