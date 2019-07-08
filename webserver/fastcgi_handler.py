import socket
import os
import struct
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
def send_params(sock, params):
    body = b''
    for k, v in params.items():
        name = bytes(k, 'ascii')
        value = bytes(v, 'ascii')
        body += struct.pack('!II', len(name) | (1 << 31), len(value) | (1 << 31))
        body += name
        body += value
    sock.sendall(struct.pack('!BBHHBx', 1, RecordType.PARAMS, 1, len(body), 0))
    sock.sendall(body)
    sock.sendall(struct.pack('!BBHHBx', 1, RecordType.PARAMS, 1, 0, 0))

async def handler(request, response):
    global fcgi_sock
    params = dict(BASE_PARAMS)
    params['REQUEST_METHOD'] = request.method
    params['PATH_INFO'] = get_path(request.uri)
    params['SERVER_PROTOCOL'] = request.http_version
    params['CONTENT_LENGTH'] = request.headers.get('content-length', '')
    params['CONTENT_TYPE'] = request.headers.get('content-type', '')
    for name, value in request.headers.items():
        params['HTTP_' + name.upper().replace('-', '_')] = value
    fcgi_sock.sendall(struct.pack('!BBHHBx', 1, RecordType.BEGIN_REQUEST, 1, 8, 0))
    fcgi_sock.sendall(struct.pack('!HBxxxxx', 1, 0))
    send_params(fcgi_sock, params)
    fcgi_sock.recv(8)
    while True:
        b = fcgi_sock.recv(1000000)
        if not b:
            break
        await response.write(b'HTTP/1.1 ' + b)


def get_handler(opts):
    global fcgi_sock
    global BASE_PARAMS
    BASE_PARAMS['SERVER_NAME'] = opts['name']
    BASE_PARAMS['SERVER_PORT'] = opts['port']
    fcgi_sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    fcgi_sock.connect('./sock')
    return handler