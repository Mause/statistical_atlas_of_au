import re
import struct
import ctypes
from queue import Queue

base = (
    'D:\\stats_data\\cache\\saau\\sections\\'
    'geology\\48006_shp\\globalmap2001\\Raster\\elevation\\'
    'elscnf'
)
NUM_RE = re.compile(r'(\d*)')
STR_RE = re.compile(r'([A-Za-z0-9_ -]*)')
PUNC = set('{},:')

sample = '{16:clabel,1:LheaderPtr,}Ehfa_HeaderTag,'
multiple = '{1:lwidth,1:lheight,1:e3:thematic,athematic,fft of real-valued data,layerType,1:e13:u1,u2,u4,u8,s8,u16,s16,u32,s32,f32,f64,c64,c128,pixelType,1:lblockWidth,1:lblockHeight,}Eimg_Layer,'
# big = '''{16:clabel,1:LheaderPtr,}Ehfa_HeaderTag,{1:LfreeList,1:lfreeSize,}Ehfa_FreeListNode,{1:lsize,1:Lptr,}Ehfa_Data,{1:lwidth,1:lheight,1:e3:thematic,athematic,fft of real-valued data,layerType,1:e13:u1,u2,u4,u8,s8,u16,s16,u32,s32,f32,f64,c64,c128,pixelType,1:lblockWidth,1:lblockHeight,}Eimg_Layer,{1:lwidth,1:lheight,1:e3:thematic,athematic,fft of real-valued data,layerType,1:e13:u1,u2,u4,u8,s8,u16,s16,u32,s32,f32,f64,c64,c128,pixelType,1:lblockWidth,1:lblockHeight,}Eimg_Layer_SubSample,{1:e2:raster,vector,type,1:LdictionaryPtr,}Ehfa_Layer,{1:sfileCode,1:Loffset,1:lsize,1:e2:false,true,logvalid,1:e2:no compression,ESRI GRID compression,compressionType,}Edms_VirtualBlockInfo,{1:lmin,1:lmax,}Edms_FreeIDList,{1:lnumvirtualblocks,1:lnumobjectsperblock,1:lnextobjectnum,1:e2:no compression,RLC compression,compressionType,0:poEdms_VirtualBlockInfo,blockinfo,0:poEdms_FreeIDList,freelist,1:tmodTime,}Edms_State,{0:pcstring,}Emif_String,{1:oEmif_String,algorithm,0:poEmif_String,nameList,}Eimg_RRDNamesList,{1:oEmif_String,projection,1:oEmif_String,units,}Eimg_MapInformation,{1:oEmif_String,dependent,}Eimg_DependentFile,{1:oEmif_String,ImageLayerName,}Eimg_DependentLayerName,{1:lnumrows,1:lnumcolumns,1:e13:EGDA_TYPE_U1,EGDA_TYPE_U2,EGDA_TYPE_U4,EGDA_TYPE_U8,EGDA_TYPE_S8,EGDA_TYPE_U16,EGDA_TYPE_S16,EGDA_TYPE_U32,EGDA_TYPE_S32,EGDA_TYPE_F32,EGDA_TYPE_F64,EGDA_TYPE_C64,EGDA_TYPE_C128,datatype,1:e4:EGDA_SCALAR_OBJECT,EGDA_TABLE_OBJECT,EGDA_MATRIX_OBJECT,EGDA_RASTER_OBJECT,objecttype,}Egda_BaseData,{1:*bvalueBD,}Eimg_NonInitializedValue,{1:oEmif_String,fileName,2:LlayerStackValidFlagsOffset,2:LlayerStackDataOffset,1:LlayerStackCount,1:LlayerStackIndex,}ImgExternalRaster,{1:*bvalidFlags,}ImgValidFlags,{1:llayerStackCount,1:lwidth,1:lheight,1:lblockWidth,1:lblockHeight,1:e13:u1,u2,u4,u8,s8,u16,s16,u32,s32,f32,f64,c64,c128,pixelType,}ImgExternalLayerStackHeader,{1:LspaceUsedForRasterData,}ImgFormatInfo831,'''


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

            if comma != ',':
                # okay, multiple elements

                n_elems = int(name[1:])

                yield (
                    length,
                    [
                        {
                            'type': name[0],
                            'name': tokens.pop(0) or tokens.pop(0)
                        }
                        for _ in range(n_elems)
                    ]
                )

                assert tokens.pop(0) == ','

            else:
                assert comma == ','

                yield (length, [{'type': name[0], 'name': name[1:]}])

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
