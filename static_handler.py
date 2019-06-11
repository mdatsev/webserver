from pathlib import Path

ROOT_DIR = Path.cwd()

def get_path(uri):
    # todo
    return ROOT_DIR.joinpath(normalize_uri(uri).strip('/'))

def normalize_uri(uri):
    # todo https://en.wikipedia.org/wiki/URL_normalization
    return uri

def handler(request):
    path = get_path(request.uri)
    if(path.is_file()):
        content = path.read_bytes()
        return bytes('HTTP/1.1 200 OK\r\nContent-Length:' + str(len(content)) + '\r\n\r\n', 'ascii') + content 
    else:
        return b'HTTP/1.1 404 Not Found\r\n\r\n'