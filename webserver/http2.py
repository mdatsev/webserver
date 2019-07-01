from enum import IntEnum
# int from bytes network order
def ifb(data):
    return int.from_bytes(data, byteorder='big')

class ByteIntEnum(IntEnum):
    @classmethod
    def _missing_(cls, arg):
        if(isinstance(arg, int)):
            return cls(arg)
        if(isinstance(arg, bytes)):
            return cls(ifb(arg))

class FrameType(ByteIntEnum):
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

class Settings(ByteIntEnum):
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
    I = data[0]
    if I < 2 ** prefix - 1:
        return I
    else:
        M = 0
        for B in data[1:]:
            I = I + (B & 127) * 2 ** M
            M = M + 7
            if B & 128 != 128:
                return I
    raise Exception('Unexpected end of integer')

async def connection_handler(reader, writer):
    current_settings = get_default_settings()
    data = await reader.readexactly(24)
    preface = ifb(data)
    if(preface != 0x505249202a20485454502f322e300d0a0d0a534d0d0a0d0a):
        raise Exception('invalid http/2 preface sent by client')
    print('http 2 connected')
    while True:
        header = await reader.readexactly(9)
        length = ifb(header[ :3])
        frame_type = FrameType(header[3:4])
        flags =  ifb(header[4:5])
        stream_id =  ifb(header[5: ]) & ~(1 << 31)
        print(frame_type, stream_id, flags, length)
        payload = await reader.readexactly(length)
        if(frame_type == FrameType.SETTINGS):
            for i in range(0, length, 6):
                identifier = Settings(payload[i:i+2])
                value = ifb(payload[i+2:i+7])
                print('\t', identifier, value)
                current_settings[identifier] = value
        elif(frame_type == FrameType.WINDOW_UPDATE):
            window_increment = ifb(payload) & ~(1 << 31)
            print(f'\twindow_increment: {window_increment}')
        elif(frame_type == FrameType.HEADERS):
            x = payload[0]
            if x & (1 << 7): # 5.2.  String Literal Representation
                index = x & ~(1 << 7)
                print(index)
            for p in payload:
                print(f'{p:#010b}')
            # elif x & 0b1100_0000 == 0b0100_0000:
            #     index = x & 0b0011_1111
            #     if index == 0:

            #     else 

            #     value_length = 
            #     print(index)
