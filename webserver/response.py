import zlib

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
        else:
            raise Exception(f'Unsupported encoding "{encoding}"')
        self.headers['Content-Encoding'] = encoding
        return self
