from pathlib import Path
from .utils import get_path
from . import logging
from .response import HTTPResponse

def get_fs_path(uri):
    global ROOT_DIR
    return ROOT_DIR.joinpath(get_path(uri)[1:])

def handler(request):
    path = get_fs_path(request.uri)
    print(path)
    if(path.is_file()):
        logging.log(f'[{request.method} {request.uri}] -> {path}')
        content = path.read_bytes()
        return HTTPResponse(
            'HTTP/1.1', 
            '200 OK', 
            { 'Content-Length:': str(len(content)) },
            content
        ) 
    else:
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