from pathlib import Path
from .utils import get_path
from . import logging
from .response import HTTPResponse
import aiofiles

def get_fs_path(uri):
    global ROOT_DIR
    return ROOT_DIR.joinpath(get_path(uri)[1:])

async def handler(request, response):
    path = get_fs_path(request.uri)
    if(path.is_file()):
        await logging.log(f'[{request.method} {request.uri}] -> {path}')
        await response.write_status('200 OK')
        await response.write_headers({'Content-Length': str(path.stat().st_size)})
        async with aiofiles.open(path, mode='rb') as f:
            while True:
                data = await f.read(1000000)
                if not data:
                    break
                await response.write_body(data)
    else:
        await logging.log(f'[{request.method} {request.uri}] -> 404 NOT FOUND [{path}]')
        await response.send( 
            '404 Not Found', 
            {},
            b'The resource was not found!'
        )

async def get_handler(opts):
    global ROOT_DIR
    ROOT_DIR = Path(opts.get('root_dir', Path.cwd()))
    return handler