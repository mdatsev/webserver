import os, sys
import importlib.util

def load_application(path):
    spec = importlib.util.spec_from_file_location('application', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.application

def handler(request):
    global BASE_ENV
    env = dict(BASE_ENV)
    env['REQUEST_METHOD'] = request.method
    env['PATH_INFO'] = request.uri # todo path not uri

    response = b''
    def write(data):
        nonlocal response
        response += data

    def start_response(status, response_headers, exc_info=None):
        nonlocal response
        response += bytes(
            'HTTP/1.1' + 
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