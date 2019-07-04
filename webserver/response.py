import zlib
import brotli
from . import logging

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
            logging.warn(f'unsupported encoding "{encoding}". ignoring')
            return
        self.headers['content-encoding'] = encoding
        return self

class HTTPStreamResponse:
    def __init__(self, http_version, writer):
        self.http_version = http_version
        self.writer = writer
        self.status_written = False
        self.headers_written = False

    async def write(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def write_status(self, status):
        assert(not self.status_written)
        await self.write(bytes(self.http_version + ' ' + status + '\r\n', 'ascii'))
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

    async def write_body(self, body):
        if not self.headers_written:
            await self.write(b'\r\n')
            self.headers_written = True
        await self.write(body)

    async def send(self, status, headers, body):
        await self.write_status(status)
        await self.write_headers(headers)
        await self.write_body(body)