import socket, asyncio
import re
from . import logging
from .config import config
from .load_handler import load_handler
host = config.get('host', '127.0.0.1') 
port = config.get('port', 8080)
handler = load_handler(config.get('handler', 'static'), 
                       config.get('handler_opts', {}))

class HTTPRequest:
    def __init__(self, method, uri, http_version, headers):
        self.method = method
        self.uri = uri
        self.http_version = http_version
        self.headers = headers
    def set_body(self, body):
        self.body = body

start_re = re.compile('^(.*?) (.*?) (.*?)\r\n(.*?\r\n)?\r\n', re.S)
header_re = re.compile('(.*?):[\t ]*(.*)')
def parse_request_start(request):
    request = request.decode('ascii') # not sure
    method, uri, version, headers = start_re.match(request).groups()
    headers = dict((header_re.match(h).groups() for h in headers.split('\r\n') if h)) if headers else {}
    return HTTPRequest(method, uri, version, headers)

async def connection_handler(reader, writer):
    buffer = b''
    body_start = 0
    while True:
        data = await reader.read(1024)
        if not data:
            break
        buffer += data
        find_start = max(0, len(buffer) - len(data) - 3)
        idx = buffer.find(b'\r\n\r\n', find_start)
        if not body_start and idx >= 0:
            body_start = idx + 4
            request = parse_request_start(buffer)
            if 'Content-Length' in request.headers:
                body_length = int(request.headers['Content-Length'])
            else:
                body_length = 0
        if body_start and len(buffer) >= body_start + body_length:
            request.set_body(buffer[body_start:body_start+body_length])
            break
    response = handler(request).encode_body('gzip').get_raw()
    writer.write(response)
    await writer.drain()
    writer.close()

def main():
    logging.log(f'Serving on http://{host}:{port}')
    loop = asyncio.get_event_loop()
    coro = asyncio.start_server(connection_handler, host, port, loop=loop)
    server = loop.run_until_complete(coro)
    loop.run_forever()
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()

if __name__ == "__main__":
    main()