def log(msg, c=''):
    print '{}{}'.format(c, msg)

def slog(msg):
    log(msg, '-=> ')

def clog(msg):
    log(msg, '<=- ')
