import aiofiles
import datetime

LOGFILE = None
def set_logging_defaults(logfile): ## level, include line, time format, message format
    global LOGFILE
    LOGFILE = logfile

class Logger:
    def __init__(self, name, logfile=LOGFILE):
        self.name = name
        self.logfile = logfile

    async def write(self, msg):
        if self.logfile:
            async with aiofiles.open(self.logfile, mode='a') as f:
                await f.write(msg)
        else:
            print(msg) # todo async?

    def write_sync(self, msg):
        if self.logfile:
            with open(self.logfile, mode='a') as f:
                f.write(msg)
        else:
            print(msg)
    
    def format(self, level, msg):
        time = datetime.datetime.now().time()
        return f'{time} [{level}] ({self.name}) {msg}'

    async def log(self, message):
        await self.write(self.format('INFO', message))

    async def warn(self, message):
        await self.write(self.format('WARN', message))

    async def error(self, message):
        await self.write(self.format('ERROR', message))

    def log_sync(self, message):
        self.write_sync(self.format('INFO', message))

    def warn_sync(self, message):
        self.write_sync(self.format('WARN', message))

    def error_sync(self, message):
        self.write_sync(self.format('ERROR', message))