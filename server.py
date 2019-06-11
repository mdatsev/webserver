#!/usr/bin/env python3

import socket
import re
from handler import handler

HOST = '127.0.0.1'
PORT = 8080

class HTTPRequest:
    def __init__(self, method, uri, http_version, headers):
        self.method = method
        self.uri = uri
        self.http_version = http_version
        self.headers = headers
    def set_body(self, body):
        self.body = body

start_re = re.compile('^(?:(.*?) (.*?) (.*?))\r\n(.*?)\r\n\r\n', re.S)
header_re = re.compile('(.*?):[\t ]*(.*)')
def parse_request_start(request):
    request = request.decode('ascii') # not sure
    method, uri, version, headers = start_re.match(request).groups()
    headers = dict(header_re.match(h).groups() for h in headers.split('\r\n'))
    return HTTPRequest(method, uri, version, headers)

def connection_handler(socket):
    conn, addr = socket
    with conn:
        buffer = b''
        body_start = 0
        while True:
            data = conn.recv(1024)
            if not data:
                break
            buffer += data
            idx = data.find(b'\r\n\r\n')
            if not body_start and idx > 0:
                body_start = idx + 4
                request = parse_request_start(buffer)
                if 'Content-Length' in request.headers:
                    body_length = int(request.headers['Content-Length'])
                else:
                    body_length = 0
            if body_start and len(data) >= body_start + body_length:
                request.set_body(buffer[body_start:body_start+body_length])
                break
        conn.sendall(handler(request))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen()
    while True:
        socket = s.accept()
        connection_handler(socket)