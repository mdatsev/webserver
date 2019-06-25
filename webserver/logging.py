n = 0
avg = 0
def measure_time(t):
    global n, avg
    avg = (t + n*avg)/(n+1)
    n += 1
    if(n % 100 == 1):
        print(avg*1000, 'ms')

def log(message):
    print(message)

def warn(message):
    print('WARN', message)

def error(message):
    print('ERROR', message)