from enum import IntEnum, IntFlag
import binascii
from . import huffman
from .header_table import HeaderTable

# int from bytes network order
def ifb(data):
    return int.from_bytes(data, byteorder='big')

class ByteEnum(IntEnum):
    @classmethod
    def _missing_(cls, arg):
        if(isinstance(arg, bytes)):
            arg = ifb(arg)
        return cls(arg)

class ByteFlag(IntFlag):
    @classmethod
    def _missing_(cls, arg):
        if(isinstance(arg, bytes)):
            arg = ifb(arg)
        return super()._missing_(arg)

class FrameType(ByteEnum):
    DATA = 0x0
    HEADERS = 0x1
    PRIORITY = 0x2
    RST_STREAM = 0x3
    SETTINGS = 0x4
    PUSH_PROMISE = 0x5
    PING = 0x6
    GOAWAY = 0x7
    WINDOW_UPDATE = 0x8
    CONTINUATION = 0x9

class HeaderFlag(ByteFlag):
    END_STREAM = 0x1
    END_HEADERS = 0x4
    PADDED = 0x8
    PRIORITY = 0x20

class Settings(ByteEnum):
    HEADER_TABLE_SIZE = 0x1
    ENABLE_PUSH = 0x2
    MAX_CONCURRENT_STREAMS = 0x3
    INITIAL_WINDOW_SIZE = 0x4
    MAX_FRAME_SIZE = 0x5
    MAX_HEADER_LIST_SIZE = 0x6



def get_default_settings():
    return {
        Settings.HEADER_TABLE_SIZE: 4096,
        Settings.ENABLE_PUSH: 1,
        Settings.MAX_CONCURRENT_STREAMS: float('inf'),
        Settings.INITIAL_WINDOW_SIZE: 65535,
        Settings.MAX_FRAME_SIZE: 16384,
        Settings.MAX_HEADER_LIST_SIZE: float('inf')
    }

def decode_var_int(data, prefix): # 5.1.  Integer Representation
    N = prefix
    I = data[0] & (2 ** N - 1)
    if I < 2 ** N - 1:
        return I, 1
    else:
        M = 0
        for i, B in enumerate(data[1:]):
            I = I + (B & 127) * 2 ** M
            M = M + 7
            if B & 128 != 128:
                return I, i + 2
    raise Exception('Unexpected end of integer')

def get_literal_name_value(table, field, prefix):
    index, _ = decode_var_int(field, prefix)
    if index == 0:
        huff = bool(field[1] & (1 << 7))
        name_len, nbytes = decode_var_int(field[1:], 7)
        value_len_start = nbytes + name_len
        name = field[nbytes:value_len_start]
        if(huff):
            name = huffman.decode(name)
    else:
        value_len_start = 1
        name = table.get_name(index)
    huff = bool(field[value_len_start] & (1 << 7))
    value_len, nbytes = decode_var_int(field[value_len_start:], 7)
    value_start = value_len_start+nbytes
    value = field[value_start:value_start+value_len]
    if(huff):
        value = huffman.decode(value)
    return name, value, value_start + value_len 

async def connection_handler(reader, writer):
    current_settings = get_default_settings()
    current_table = HeaderTable()
    data = await reader.readexactly(24)
    preface = ifb(data)
    if(preface != 0x505249202a20485454502f322e300d0a0d0a534d0d0a0d0a):
        raise Exception('invalid http/2 preface sent by client')
    print('----http 2 connected----')
    while True:
        header = await reader.readexactly(9)
        length = ifb(header[ :3])
        frame_type = FrameType(header[3])
        flags = header[4]
        stream_id =  ifb(header[5: ]) & ~(1 << 31)
        print(f'{frame_type.name}: flags={flags}, stream={stream_id}, length={length}')
        payload = await reader.readexactly(length)
        if(frame_type == FrameType.SETTINGS):
            for i in range(0, length, 6):
                identifier = Settings(payload[i:i+2])
                value = ifb(payload[i+2:i+7])
                print('\t', identifier, value)
                current_settings[identifier] = value
        elif(frame_type == FrameType.WINDOW_UPDATE):
            window_increment = ifb(payload) & ~(1 << 31)
            print(f'\twindow_increment={window_increment}')
        elif(frame_type == FrameType.HEADERS):
            flags = HeaderFlag(flags)
            payload = b'\x48\x82\x64\x02\x58\x85\xae\xc3\x77\x1a\x4b\x61\x96\xd0\x7a\xbe\x94\x10\x54\xd4\x44\xa8\x20\x05\x95\x04\x0b\x81\x66\xe0\x82\xa6\x2d\x1b\xff\x6e\x91\x9d\x29\xad\x17\x18\x63\xc7\x8f\x0b\x97\xc8\xe9\xae\x82\xae\x43\xd3'
            i = 0
            while True:
                field = payload[i:]
                if len(field) == 0:
                    break
                x = field[0]
                if x & (1 << 7): # 5.2.  String Literal Representation
                    index, _ = decode_var_int(field, 7)
                    print(f'\tindex: index={index}')
                    i += 1
                elif x & 0b1100_0000 == 0b0100_0000: # 6.2.1.  Literal Header Field with Incremental Indexing
                    name, value, length = get_literal_name_value(current_table, field, 6)
                    i += length
                    print(f'\tindexing: {name}: {value}')
                elif x & 0b1111_0000 == 0b0000_0000: # 6.2.2.  Literal Header Field without Indexing
                    name, value, length = get_literal_name_value(current_table, field, 4)
                    i += length
                    print(f'\tno indexing: {name}: {value}')
                elif x & 0b1111_0000 == 0b0001_0000: # 6.2.3.  Literal Header Field Never Indexed
                    name, value, length = get_literal_name_value(current_table, field, 4)
                    i += length
                    print(f'\tnever indexed: {name}: {value}')
            if(flags & HeaderFlag.END_STREAM):
                print('----request done----')