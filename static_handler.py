from pathlib import Path
import urllib

ROOT_DIR = Path.cwd()

def normalize_uri(uri):
    uri = uri.lower()
    uri = urllib.parse.urlparse(uri)
    return uri._replace(path=urllib.parse.unquote(uri.path))

def remove_dot_segments(path):
    input = path.strip('/').split('/')
    output = []
    for seg in input:
        if seg == '.':
            continue
        if seg == '..':
            if(len(output) > 0):
                output.pop()
            continue
        output.append(seg)
    return output

def get_path(uri):
    uri = normalize_uri(uri)
    return ROOT_DIR.joinpath(ROOT_DIR, *remove_dot_segments(uri.path))

def handler(request):
    path = get_path(request.uri)
    if(path.is_file()):
        content = path.read_bytes()
        return bytes('HTTP/1.1 200 OK\r\nContent-Length:' + str(len(content)) + '\r\n\r\n', 'ascii') + content 
    else:
        return b'HTTP/1.1 404 Not Found\r\n\r\n'