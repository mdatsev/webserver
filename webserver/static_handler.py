from pathlib import Path
from .utils import get_path
from . import logging
from .response import HTTPResponse

if False:
    import aiofiles
    def async_open(path):
        return aiofiles.open(path, mode='rb')
    def async_read(f, _):
        return f.read(16_000_000)
else:
    from aiofile import AIOFile
    def async_open(path):
        return AIOFile(path, 'rb')
    def async_read(f, offset):
        return f.read(8_000_000, offset)


def get_fs_path(uri):
    global ROOT_DIR
    return ROOT_DIR.joinpath(get_path(uri)[1:])

async def handler(request, response):
    path = get_fs_path(request.uri)
    if(path.is_file()):
        logging.log(f'[{request.method} {request.uri}] -> {path}')
        await response.write_status('200 OK')
        await response.write_headers({'Content-Length': str(path.stat().st_size)})
        async with async_open(path) as f:
            offset = 0
            while True:
                data = await async_read(f, offset)
                offset += len(data)
                if not data:
                    break
                await response.write_body(data)
    else:
        logging.log(f'[{request.method} {request.uri}] -> 404 NOT FOUND [{path}]')
        response.send( 
            '404 Not Found', 
            {},
            b'The resource was not found!'
        )

def get_handler(opts):
    global ROOT_DIR
    ROOT_DIR = Path(opts.get('root_dir', Path.cwd()))
    return handler