import socket, asyncio, ssl, re
import time
from . import logging
from .config import config
from .load_handler import load_handler
host = config.get('host', '127.0.0.1') 
port = config.get('port', 8080)
handler = load_handler(config.get('handler', 'static'), 
                       config.get('handler_opts', {}))
use_https = config.get('use_https', False)
ssl_context = None
if use_https:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        config.get('https_cert'), 
        config.get('https_key'),
        config.get('https_password', None)
    )

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
    headers = {
        k.lower(): v 
        for k, v in (
            header_re.match(h).groups() 
            for h in headers.split('\r\n') if h)
    } if headers else {}
    return HTTPRequest(method, uri, version, headers)

async def connection_handler(reader, writer):
    start_time = time.time()
    buffer = b''
    body_start = 0
    while True:
        data = await reader.read(1024)
        if not data:
            logging.warn('connection closed. aborting')
            return
        buffer += data
        find_start = max(0, len(buffer) - len(data) - 3)
        idx = buffer.find(b'\r\n\r\n', find_start)
        if not body_start and idx >= 0:
            body_start = idx + 4
            request = parse_request_start(buffer)
            if 'content-length' in request.headers:
                body_length = int(request.headers['content-length'])
            else:
                body_length = 0
        if body_start and len(buffer) >= body_start + body_length:
            request.set_body(buffer[body_start:body_start+body_length])
            break
    if(request.uri == '/ram_test'):
        response = b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello'
    else:
        response = (await handler(request)).get_raw()
    writer.write(response)
    await writer.drain()
    writer.close()
    elapsed_time = time.time() - start_time
    logging.measure_time(elapsed_time)

def main():
    try:
        loop = asyncio.get_event_loop()
        coro = asyncio.start_server(connection_handler, host, port, loop=loop, ssl=ssl_context)
        server = loop.run_until_complete(coro)
        logging.log(f'Serving on {"https" if use_https else "http"}://{host}:{port}')
        while True:
            try:
                loop.run_forever()
            except Exception as e:
                logging.error(e)
    except Exception as e:
        logging.error('Unrecoverable error')
    except KeyboardInterrupt:
        logging.log_performance()
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()