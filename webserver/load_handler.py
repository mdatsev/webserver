async def load_handler(handler_type, handler_opts):
    if handler_type == 'static':
        from .static_handler import get_handler, handler_cleanup
    elif handler_type == 'wsgi':
        from .wsgi_handler import get_handler, handler_cleanup
    elif handler_type == 'router':
        from .router_handler import get_handler, handler_cleanup
    elif handler_type == 'fastcgi':
        from .fastcgi_handler import get_handler, handler_cleanup
    else:
        raise Exception(f'Unknown handler "{handler_type}"')
    return await get_handler(handler_opts), handler_cleanup