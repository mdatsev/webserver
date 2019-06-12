from pathlib import Path
import urllib

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

def get_path(uri, root_dir):
    uri = normalize_uri(uri)
    return root_dir.joinpath(root_dir, *remove_dot_segments(uri.path))

def handler(request, opts):
    root_dir = Path(opts.get('root_dir', Path.cwd()))
    path = get_path(request.uri, root_dir)
    if(path.is_file()):
        content = path.read_bytes()
        return bytes('HTTP/1.1 200 OK\r\nContent-Length:' + str(len(content)) + '\r\n\r\n', 'ascii') + content 
    else:
        return b'HTTP/1.1 404 Not Found\r\n\r\n'