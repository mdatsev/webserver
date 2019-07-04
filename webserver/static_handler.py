from pathlib import Path
from .utils import get_path
from . import logging
from .response import HTTPResponse
import aiofiles

def get_fs_path(uri):
    global ROOT_DIR
    return ROOT_DIR.joinpath(get_path(uri)[1:])

async def handler(request):
    path = get_fs_path(request.uri)
    if(path.is_file()):
        logging.log(f'[{request.method} {request.uri}] -> {path}')
        async with aiofiles.open(path, mode='rb') as f:
            content = await f.read()
        return HTTPResponse(
            'HTTP/1.1', 
            '200 OK', 
            { 'Content-Length': str(len(content)) },
            content
        ) 
    else:
        logging.log(f'[{request.method} {request.uri}] -> 404 NOT FOUND [{path}]')
        return HTTPResponse(
            'HTTP/1.1', 
            '404 Not Found', 
            {},
            b'The resource was not found!'
        )

def get_handler(opts):
    global ROOT_DIR
    ROOT_DIR = Path(opts.get('root_dir', Path.cwd()))
    return handler