import os, sys
import importlib.util
import io
from utils import get_path

def load_application(path):
    module_dir = os.path.dirname(path)
    sys.path.append(module_dir)
    os.chdir(module_dir)
    spec = importlib.util.spec_from_file_location('application', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.application

def handler(request):
    global BASE_ENV
    env = dict(BASE_ENV)
    env['REQUEST_METHOD'] = request.method
    env['PATH_INFO'] = '/' + get_path(request.uri)
    env['SERVER_PROTOCOL'] = request.http_version
    env['CONTENT_LENGTH'] = request.headers.get('Content-Length', '')
    env['CONTENT_TYPE'] = request.headers.get('Content-Type', '')
    env['wsgi.input'] = io.BytesIO(request.body)
    for name, value in request.headers.items():
        env['HTTP_' + name.upper().replace('-', '_')] = value

    response = b''
    def write(data):
        nonlocal response
        response += data

    def start_response(status, response_headers, exc_info=None):
        nonlocal response
        response += bytes(
            request.http_version + 
            ' ' + 
            status +
            '\r\n' +
            '\r\n'.join(map(lambda h: h[0] + ': ' + h[1], response_headers)) +
            '\r\n\r\n', 'ascii'
        )
        return write

    result = application(env, start_response)
    try:
        for data in result:
            if data:
                write(data)
    finally:
        if hasattr(result, 'close'):
            result.close()
        return response
    

def get_handler(opts):
    global application
    application = load_application(opts['application'])
    global BASE_ENV
    BASE_ENV = dict(os.environ.items())
    BASE_ENV['wsgi.version']      = (1, 0)
    BASE_ENV['wsgi.url_scheme']   = 'http'
    BASE_ENV['wsgi.errors']       = sys.stderr
    BASE_ENV['wsgi.multithread']  = False
    BASE_ENV['wsgi.multiprocess'] = False
    BASE_ENV['wsgi.run_once']     = False
    BASE_ENV['SERVER_NAME']       = opts['name']
    BASE_ENV['SERVER_PORT']       = opts['port']
    return handler