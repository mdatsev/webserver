import urllib.parse

def normalize_uri(uri):
    uri = urllib.parse.urlparse(uri)
    uri = uri._replace(netloc=uri.netloc.lower())
    return uri._replace(path=urllib.parse.unquote(uri.path))

def remove_dot_segments(path):
    input = path.split('/')
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
    return '/'.join(remove_dot_segments(normalize_uri(uri).path))