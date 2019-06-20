from .utils import get_path
from . import logging
from .load_handler import load_handler

def handler(request):
    path = get_path(request.uri)
    for route, handler in routes.items():
        if path.startswith(route):
            request.uri = path[len(route) - 1:]
            return handler(request)
    return b'HTTP/1.1 404 Not Found\r\n\r\n'
    

def get_handler(opts):
    global routes
    routes = opts['routes']
    routes = {k: load_handler(v['handler'], v['handler_opts']) for k, v in routes.items()}
    return handler