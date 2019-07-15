import aiofiles
import datetime
import sys

ACCESS_LOG = None
ERROR_LOG = None
def set_logging_defaults(access_log, error_log): ## level, include line, time format, message format
    global ACCESS_LOG
    global ERROR_LOG
    ACCESS_LOG = access_log
    ERROR_LOG = error_log

def get_date_str():
    return datetime.datetime.now(datetime.timezone.utc).astimezone().strftime('%d/%b/%Y:%H:%M:%S %z')

def format_log(ip, requestline, responsecode):
    return f'''{ip} - - [{get_date_str()}] "{requestline}" {responsecode} -\n'''

class Logger:
    def __init__(self, name):
        self.name = name

    async def write(self, msg):
        if ACCESS_LOG:
            async with aiofiles.open(ACCESS_LOG, mode='a') as f:
                await f.write(msg)
        else:
            print(msg, end='') # todo async?

    def write_sync(self, msg):
        if ACCESS_LOG:
            with open(ACCESS_LOG, mode='a') as f:
                f.write(msg)
        else:
            print(msg, end='')

    async def write_error(self, msg):
        if ERROR_LOG:
            async with aiofiles.open(ERROR_LOG, mode='a') as f:
                await f.write(msg)
        else:
            print(msg, file=sys.stderr, end='') # todo async?

    def write_error_sync(self, msg):
        if ERROR_LOG:
            with open(ERROR_LOG, mode='a') as f:
                f.write(msg)
        else:
            print(msg, file=sys.stderr, end='')
    
    def format(self, level, msg):
        return f'[{get_date_str()}] [{self.name}] [{level}] {msg}\n'

    async def log(self, *args, **kwargs):
        await self.write(format_log(*args, **kwargs))

    async def info(self, message):
        await self.write_error(self.format('INFO', message))

    async def warn(self, message):
        await self.write_error(self.format('WARN', message))

    async def error(self, message):
        await self.write_error(self.format('ERROR', message))

    def log_sync(self, message):
        self.write_sync(format_log(*args, **kwargs))

    def info_sync(self, message):
        self.write_error_sync(self.format('INFO', message))

    def warn_sync(self, message):
        self.write_error_sync(self.format('WARN', message))

    def error_sync(self, message):
        self.write_error_sync(self.format('ERROR', message))