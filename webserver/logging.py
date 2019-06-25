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

def log_performance():
    global n
    if(n > 0):    
        print('\n\n')
        print('min:', format_time(mint))
        print('avg:', format_time(avg))
        print('max:', format_time(maxt))

def log(message):
    print(message)

def warn(message):
    print('WARN', message)

def error(message):
    print('ERROR', message)