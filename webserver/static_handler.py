from pathlib import Path
from .utils import normalize_uri, remove_dot_segments
from . import logging

def get_fs_path(uri):
    global ROOT_DIR
    uri = normalize_uri(uri)
    return ROOT_DIR.joinpath(*remove_dot_segments(uri.path))

def handler(request):
    path = get_fs_path(request.uri)
    if(path.is_file()):
        logging.log(f'[{request.method} {request.uri}] -> {path}')
        content = path.read_bytes()
        return bytes('HTTP/1.1 200 OK\r\nContent-Length:' + str(len(content)) + '\r\n\r\n', 'ascii') + content 
    else:
        return b'HTTP/1.1 404 Not Found\r\n\r\n'

def get_handler(opts):
    global ROOT_DIR
    ROOT_DIR = Path(opts.get('root_dir', Path.cwd()))
    return handler