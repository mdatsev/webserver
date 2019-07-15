import socket
import os
import struct
import subprocess
import time
import os
import asyncio
from collections import defaultdict
from enum import IntEnum
from .utils import get_path
from logging import Logger
from .response import HTTPResponse

logger = Logger('handler fastcgi')

class RecordType(IntEnum):
    BEGIN_REQUEST = 1
    ABORT_REQUEST = 2
    END_REQUEST = 3
    PARAMS = 4
    STDIN = 5
    STDOUT = 6
    STDERR = 7
    DATA = 8
    GET_VALUES = 9
    GET_VALUES_RESULT = 10
    UNKNOWN_TYPE = 11

def make_record(type, rid, body=b'', version=1):
    header = struct.pack('!BBHHBx', version, type, rid, len(body), 0)
    return header + body

BASE_PARAMS = {}
async def send_params(writer, params, rid):
    body = b''
    for k, v in params.items():
        name = bytes(k, 'ascii')
        value = v if isinstance(v, bytes) else bytes(v, 'ascii') 
        body += struct.pack('!II', len(name) | (1 << 31), len(value) | (1 << 31))
        body += name
        body += value
    writer.write(make_record(RecordType.PARAMS, rid, body))
    writer.write(make_record(RecordType.PARAMS, rid))

counter = 0
def get_request_id():
    global counter
    counter += 1
    return counter

async def handler(request, response):
    global reader
    global writer
    rid = get_request_id()
    params = dict(BASE_PARAMS)
    params['REQUEST_METHOD'] = request.method
    params['PATH_INFO'] = get_path(request.uri)
    params['SERVER_PROTOCOL'] = request.http_version
    params['CONTENT_LENGTH'] = request.headers.get('content-length', '')
    params['CONTENT_TYPE'] = request.headers.get('content-type', '')
    for name, value in request.headers.items():
        params['HTTP_' + name.upper().replace('-', '_')] = value
    writer.write(make_record(RecordType.BEGIN_REQUEST, rid, 
                                struct.pack('!HBxxxxx', 1, 1)))
    await send_params(writer, params, rid)
    writer.write(make_record(RecordType.STDIN, rid, request.body))
    writer.write(make_record(RecordType.STDIN, rid))
    await writer.drain()
    while True:
        rtype, data = await get_record(rid)
        if RecordType(rtype) == RecordType.STDOUT:
            if data.startswith(b'Status: '):
                status, sep, data = data.partition(b'\r\n')
                await response.write_status(status[8:])
            await response.write(data)
        if RecordType(rtype) == RecordType.END_REQUEST:
            break
    
async def get_record(rid):
    global recordq
    return await recordq[rid].get()

recordq = defaultdict(asyncio.Queue)
async def fcgi_reader():
    global reader
    global recordq
    while True:
        try:
            header = await reader.readexactly(8)
            v, rtype, rid, clen, plen = struct.unpack('!BBHHBx', header)
            content = await reader.readexactly(clen)
            padding = await reader.readexactly(plen)  
            await recordq[rid].put((rtype, content))
        except asyncio.CancelledError:
            break

async def get_handler(opts):
    global reader
    global writer
    global BASE_PARAMS
    global reader_task
    BASE_PARAMS['SERVER_NAME'] = opts['name']
    BASE_PARAMS['SERVER_PORT'] = opts['port']
    path = opts.get('application')
    module_dir = os.path.dirname(path)
    subprocess.Popen(path, cwd=module_dir)
    while True:
        try:
            reader, writer = await asyncio.open_unix_connection(path=opts.get('sock'))
            break
        except ConnectionRefusedError:
            time.sleep(0.1)
            logger.info('Connection refused. Retrying...')
    reader_task = asyncio.Task(fcgi_reader())
    return handler

async def handler_cleanup():
    global reader_task
    reader_task.cancel()