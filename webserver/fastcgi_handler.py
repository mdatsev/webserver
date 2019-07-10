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
from . import logging
from .response import HTTPResponse

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

BASE_PARAMS = {}
async def send_params(writer, params, rid):
    body = b''
    for k, v in params.items():
        name = bytes(k, 'ascii')
        value = v if isinstance(v, bytes) else bytes(v, 'ascii') 
        body += struct.pack('!II', len(name) | (1 << 31), len(value) | (1 << 31))
        body += name
        body += value
    writer.write(struct.pack('!BBHHBx', 1, RecordType.PARAMS, rid, len(body), 0))
    writer.write(body)
    writer.write(struct.pack('!BBHHBx', 1, RecordType.PARAMS, rid, 0, 0))

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
    writer.write(struct.pack('!BBHHBx', 1, RecordType.BEGIN_REQUEST, rid, 8, 0))
    writer.write(struct.pack('!HBxxxxx', 1, 1))
    await send_params(writer, params, rid)
    writer.write(struct.pack('!BBHHBx', 1, RecordType.STDIN, rid, len(request.body), 0))
    writer.write(request.body)
    writer.write(struct.pack('!BBHHBx', 1, RecordType.STDIN, rid, 0, 0))
    await writer.drain()
    while True:
        rtype, data = await get_record(rid)
        if RecordType(rtype) == RecordType.STDOUT:
                if data.startswith(b'Status:'):
                    status, sep, data = data.partition(b'\r\n')
                    await response.write(b'HTTP/1.1' + status[7:] + sep)
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
        header = b''
        while len(header) < 8:
            h = await reader.read(1)
            if not h:
                break
            header += h
        if not h:
            break
        v, rtype, rid, clen, plen = struct.unpack('!BBHHBx', header)
        data = b''
        while len(data) < clen:
            b = await reader.read(1)
            data += b
        padding = b''
        while len(padding) < plen:
            b = await reader.read(1)
            padding += b
        
        await recordq[rid].put((rtype, data))

async def get_handler(opts):
    global reader
    global writer
    global BASE_PARAMS
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
            print('fail')
    asyncio.Task(fcgi_reader())
    return handler