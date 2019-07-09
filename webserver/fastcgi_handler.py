import socket
import os
import struct
import subprocess
import time
import os
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

#           typedef struct {
#               unsigned char version;
#               unsigned char type;
#               unsigned char requestIdB1;
#               unsigned char requestIdB0;
#               unsigned char contentLengthB1;
#               unsigned char contentLengthB0;
#               unsigned char paddingLength;
#               unsigned char reserved;
#               unsigned char contentData[contentLength];
#               unsigned char paddingData[paddingLength];
#           } FCGI_Record;

#           typedef struct {
#                       unsigned char nameLengthB3;  /* nameLengthB3  >> 7 == 1 */
#                       unsigned char nameLengthB2;
#                       unsigned char nameLengthB1;
#                       unsigned char nameLengthB0;
#                       unsigned char valueLengthB3; /* valueLengthB3 >> 7 == 1 */
#                       unsigned char valueLengthB2;
#                       unsigned char valueLengthB1;
#                       unsigned char valueLengthB0;
#                       unsigned char nameData[nameLength
#                               ((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
#                       unsigned char valueData[valueLength
#                               ((B3 & 0x7f) << 24) + (B2 << 16) + (B1 << 8) + B0];
#                   } FCGI_NameValuePair44;

BASE_PARAMS = {}
def send_params(sock, params, rid):
    body = b''
    for k, v in params.items():
        name = bytes(k, 'ascii')
        value = bytes(v, 'ascii')
        body += struct.pack('!II', len(name) | (1 << 31), len(value) | (1 << 31))
        body += name
        body += value
    sock.sendall(struct.pack('!BBHHBx', 1, RecordType.PARAMS, rid, len(body), 0))
    sock.sendall(body)
    sock.sendall(struct.pack('!BBHHBx', 1, RecordType.PARAMS, rid, 0, 0))

counter = 0
def get_request_id():
    global counter
    counter += 1
    return counter

async def handler(request, response):
    global fcgi_sock
    rid = get_request_id()
    params = dict(BASE_PARAMS)
    params['REQUEST_METHOD'] = request.method
    params['PATH_INFO'] = get_path(request.uri)
    params['SERVER_PROTOCOL'] = request.http_version
    params['CONTENT_LENGTH'] = request.headers.get('content-length', '')
    params['CONTENT_TYPE'] = request.headers.get('content-type', '')
    for name, value in request.headers.items():
        params['HTTP_' + name.upper().replace('-', '_')] = value
    fcgi_sock.sendall(struct.pack('!BBHHBx', 1, RecordType.BEGIN_REQUEST, rid, 8, 0))
    fcgi_sock.sendall(struct.pack('!HBxxxxx', 1, 1))
    send_params(fcgi_sock, params, rid)
    fcgi_sock.sendall(struct.pack('!BBHHBx', 1, RecordType.STDIN, rid, len(request.body), 0))
    fcgi_sock.sendall(request.body)
    fcgi_sock.sendall(struct.pack('!BBHHBx', 1, RecordType.STDIN, rid, 0, 0))
    while True:
        header = b''
        while len(header) < 8:
            h = fcgi_sock.recv(1)
            if not h:
                break
            header += h
        if not h:
            break
        v, rtype, rid, clen, plen = struct.unpack('!BBHHBx', header)
        data = b''
        while len(data) < clen:
            b = fcgi_sock.recv(1)
            data += b
        padding = b''
        while len(padding) < plen:
            b = fcgi_sock.recv(1)
            padding += b
        if RecordType(rtype) == RecordType.STDOUT:
            if data.startswith(b'Status:'):
                status, sep, data = data.partition(b'\r\n')
                await response.write(b'HTTP/1.1' + status[7:] + sep)
            await response.write(data)
        if RecordType(rtype) == RecordType.END_REQUEST:
            break


def get_handler(opts):
    global fcgi_sock
    global BASE_PARAMS
    BASE_PARAMS['SERVER_NAME'] = opts['name']
    BASE_PARAMS['SERVER_PORT'] = opts['port']
    path = opts.get('application')
    module_dir = os.path.dirname(path)
    subprocess.Popen(path, cwd=module_dir)
    fcgi_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    while True:
        try:
            fcgi_sock.connect(opts.get('sock'))
            break
        except ConnectionRefusedError:
            time.sleep(0.1)
            print('fail')
    return handler