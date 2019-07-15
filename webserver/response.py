import zlib
import brotli
from logging import Logger

logger = Logger('response')

class HTTPResponse:
    def __init__(self, http_version, status, headers, body=b''):
        self.http_version = http_version
        self.status = status
        self.headers = headers
        self.body = body

    def write_body(self, data):
        self.body += data

    def get_raw(self):
        return bytes(
            self.http_version + 
            ' ' + 
            self.status +
            '\r\n' +
            '\r\n'.join(map(lambda h: h[0] + ': ' + h[1], self.headers.items())) +
            '\r\n\r\n', 'ascii'
        ) + self.body
    
    def encode_body(self, encoding):
        if encoding == 'identity':
            pass
        elif encoding == 'deflate':
            compress = zlib.compressobj(wbits=-zlib.MAX_WBITS)
            self.body = compress.compress(self.body) + compress.flush()
        elif encoding == 'gzip':
            compress = zlib.compressobj(wbits=zlib.MAX_WBITS|16)
            self.body = compress.compress(self.body) + compress.flush()
        elif encoding == 'br':
            self.body = brotli.compress(self.body)
        else:
            logger.warn(f'unsupported encoding "{encoding}". ignoring')
            return
        self.headers['content-encoding'] = encoding
        return self

class IdentityEncoder:
    def process(self,data):
        return data
    def flush(self):
        return b''

class DeflateEncoder:
    def process(self, data):
        return self.compressor.compress(data)
    def flush(self):
        return self.compressor.flush()
    def __init__(self):
        self.compressor = zlib.compressobj(wbits=-zlib.MAX_WBITS)

class GzipEncoder:
    def process(self, data):
        return self.compressor.compress(data)
    def flush(self):
        return self.compressor.flush()
    def __init__(self):
        self.compressor = zlib.compressobj(wbits=zlib.MAX_WBITS|16)

class BrotliEncoder:
    def process(self, data):
        return self.compressor.process(data)
    def flush(self):
        return self.compressor.flush()
    def __init__(self):
        self.compressor = brotli.Compressor()

def get_encoder(encoding):
    if encoding == 'identity':
        return IdentityEncoder()
    elif encoding == 'deflate':
        return DeflateEncoder()
    elif encoding == 'gzip':
        return GzipEncoder()
    elif encoding == 'br':
        return BrotliEncoder()
    else:
        raise Exception(f'unsupported encoding "{encoding}"')

def convert_str(f):
    def wrapper(self, arg): 
        if isinstance(arg, str):
            arg = bytes(arg, 'utf-8')
        return f(self, arg) 
    return wrapper 

class HTTPStreamResponse:
    def __init__(self, http_version, writer, encoding='identity'):
        self.http_version = bytes(http_version, 'ascii')
        self.writer = writer
        self.unsent_headers = {}
        self.encoder = get_encoder(encoding)
        self.unsent_headers['content-encoding'] = encoding
        self.status_written = False
        self.headers_written = False

    async def write(self, data):
        self.writer.write(data)
        await self.writer.drain()

    @convert_str    
    async def write_status(self, status):
        assert(not self.status_written)
        self.statuscode, _, self.statustext = status.decode('ascii').partition(' ')
        await self.write(self.http_version + b' ' + status + b'\r\n')
        self.status_written = True

    async def write_headers(self, headers):
        assert(self.status_written)
        assert(not self.headers_written)
        raw = b''
        for k, v in headers.items():
            if isinstance(v, str):
                v = bytes(v, 'ascii')
            raw += bytes(k + ': ', 'ascii') + v + b'\r\n'
        await self.write(raw)

    @convert_str
    async def write_body(self, body):
        if not self.headers_written:
            await self.write_headers(self.unsent_headers)
            await self.write(b'\r\n')
            self.headers_written = True
        await self.write(self.encoder.process(body))

    async def send(self, status, headers, body):
        await self.write_status(status)
        await self.write_headers(headers)
        await self.write_body(body)

    async def finish(self):
       await self.write(self.encoder.flush())