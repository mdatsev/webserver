def load_handler(handler_type, handler_opts):
    if handler_type == 'static':
        from .static_handler import get_handler
    elif handler_type == 'wsgi':
        from .wsgi_handler import get_handler
    elif handler_type == 'router':
        from .router_handler import get_handler
    elif handler_type == 'fastcgi':
        from .fastcgi_handler import get_handler
    else:
        raise Exception(f'Unknown handler "{handler_type}"')
    return get_handler(handler_opts)