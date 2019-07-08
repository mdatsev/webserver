import aiofiles

async def write(*args):
    async with aiofiles.open('log.txt', mode='w') as f:
        await f.write(' '.join(args) + '\n')

def write_sync(*args):
    with open('log.txt', mode='w') as f:
        f.write(' '.join(args) + '\n')


n = 0
avg = 0
mint = float('inf')
maxt = float('-inf')
def measure_time(t):
    global n, avg, mint,maxt
    avg = (t + n*avg)/(n+1)
    n += 1
    mint = min(mint, t)
    maxt = max(maxt, t)    

def format_time(t):
    return f'{t*1000:.3f}ms per request'

async def log_performance():
    global n
    if(n > 0):    
        await write('\n\n',
            'min:', format_time(mint),
            'avg:', format_time(avg),
            'max:', format_time(maxt))

async def log(message):
    await write(message)

async def warn(message):
    await write('WARN', message)

async def error(message):
    await write('ERROR', message)

def log_sync(message):
    write_sync(message)

def warn_sync(message):
    write_sync('WARN', message)

def error_sync(message):
    write_sync('ERROR', message)