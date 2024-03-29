import socket, asyncio, ssl, re
import time
import datetime
from . import logging
from .config import config
from .load_handler import load_handler
from .response import HTTPStreamResponse

logger = logging.Logger('server')

class HTTPRequest:
    def __init__(self, method, uri, http_version, headers):
        self.method = method
        self.uri = uri
        self.http_version = http_version
        self.headers = headers
    def set_body(self, body):
        self.body = body

start_re = re.compile(b'^(.*?) (.*?) (.*?)\r\n(.*?\r\n)?\r\n', re.S)
header_re = re.compile(b'(.*?):[\t ]*(.*)')
def parse_request_start(request):
    method, uri, version, headers = start_re.match(request).groups()
    headers = {
        k.lower().decode('ascii'): v 
        for k, v in (
            header_re.match(h).groups() 
        for h in headers.split(b'\r\n') if h)
    } if headers else {}
    return HTTPRequest(method.decode('ascii'), uri.decode('ascii'), version.decode('ascii'), headers)

async def connection_handler(reader, writer):
    # start_time = time.time()
    buffer = b''
    body_start = 0
    while True:
        data = await reader.read(1024)
        if not data:
            await logger.warn('connection closed. aborting')
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
        writer.write(
            b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello'b'HTTP/1.1 200 OK\r\nContent-Length: 5\r\n\r\nhello')
        await writer.drain()
    else:
        response = HTTPStreamResponse('HTTP/1.1', writer, choose_encoding(request.headers['accept-encoding'].decode('ascii')))
        try:
            await handler(request, response)
        except Exception as e:
            if not response.status_written:
                await response.send( 
                    '500 Internal Server Error', 
                    {},
                    b'500 Internal Server Error'
                )
            else:
                await logger.warn(e)
        try:
            await response.finish()
        except Exception as e:
            await logger.warn(e)
    await logger.log(
        writer.get_extra_info('peername')[0],
        f"{request.method} {request.uri} {request.http_version}".replace('"', '\\"'),
        response.statuscode)
    writer.close()
    # elapsed_time = time.time() - start_time
    # logger.measure_time(elapsed_time)

host = config.get('host', '127.0.0.1') 
port = config.get('port', 8080)
use_https = config.get('use_https', False)
encoding_list = config.get('encoding', ['identity'])
encoding_prioritize = config.get('encoding_prioritize', 'server')
def choose_encoding(accept):
    first = encoding_list
    second = [e.strip() for e in accept.split(',')]
    if encoding_prioritize == 'client':
        [first, second] = [second, first]
    for i in first:
        for j in second:
            if(i == j):
                return i
    
ssl_context = None
if use_https:
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(
        config.get('https_cert'), 
        config.get('https_key'),
        config.get('https_password', None)
    )

logging.set_logging_defaults(config.get('access_log', None), config.get('error_log', None))

async def initialize_async(loop):
    global handler
    global handler_cleanup
    handler, handler_cleanup = await load_handler(config.get('handler', 'static'), 
                       config.get('handler_opts', {}))
    server = await asyncio.start_server(connection_handler, host, port, loop=loop, ssl=ssl_context)
    return server

def main():
    global handler_cleanup
    try:
        loop = asyncio.get_event_loop()
        server = loop.run_until_complete(initialize_async(loop))
        logger.info_sync(f'Serving on {"https" if use_https else "http"}://{host}:{port}')
        while True:
            try:
                loop.run_forever()
            except Exception as e:
                logger.error_sync(e)
    except Exception as e:
        logger.error_sync(e)
    except KeyboardInterrupt:
        # logging.log_performance()
        server.close()
        loop.run_until_complete(handler_cleanup())
        loop.run_until_complete(server.wait_closed())
        loop.close()