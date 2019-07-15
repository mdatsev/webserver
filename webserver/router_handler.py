from .utils import get_path
from . import logging
from .load_handler import load_handler
from .response import HTTPResponse
import asyncio

async def handler(request, response):
    path = get_path(request.uri)
    for route, (handler, _) in routes.items():
        if path.startswith(route):
            request.uri = path[len(route) - 1:]
            return await handler(request, response)
    await response.send(
        '404 Not Found',
        {},
        b'No app on this path!'
    )
    

async def get_handler(opts):
    global routes
    routes = opts['routes']
    routes = {k: (await load_handler(v['handler'], v['handler_opts'])) for k, v in routes.items()}
    return handler

async def handler_cleanup():
    global routes
    await asyncio.gather(*(cleanup() for _, (_, cleanup) in routes.items()))