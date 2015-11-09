import telnetlib
from re import sub, split
from time import sleep
from traceback import format_exc
from Queue import Empty

from bobby import app, sio, curry_emit
from config import FICS_HOST, FICS_PORT
from logger import clog # , slog, log

#
EMIT                    = curry_emit(sio.emit)
TN                      = None
CONFIGURED              = False
TIMEOUT                 = 3
PRELIMINARY_COMMANDS    = """\
set seek 0
set bell off
set style 12
iset nowrap 1
iset ms 1
iset gameinfo 1
-channel 53
set provshow 1
set interface 'BOBBY (http://github.com/noah/bobby)'\
""".split('\n')

def is_style12(s):
    return s[:4] == '<12>'

def parse_style12(s):
    keys = "s12 row1 row2 row3 row4 row5 row6 row7 row8 turn_color\
        double_push_file white_castle_short white_castle_long\
        black_castle_short black_castle_long moves_since_irreversible\
        game_number white_name black_name my_relation initial_time_secs\
        increment_time_secs white_strength black_strength white_time_remain\
        black_time_remain next_move_number coordinate_notation\
        previous_move_time pretty_notation_previous flip_field"
    return dict(zip(keys.split(), s.split(' ')))

def fen_from_style12(s):
    #
    fen = []
    for i in xrange(1, 9):
        fen.append(s['row{}'.format(i)])
    fen = '/'.join(fen)
    #
    foo = '9' # <- fen format known not to contain this char
    fen = fen.replace('-', foo)
    fen_split = split(r'\D', fen)
    for fs in fen_split:
        l = len(fs)
        if l > 0:
            fen = sub('9+', str(l), fen, count=1)
    return fen

def fics_r(lock):
    global TN, CONFIGURED

    assert(TN is None)

    EMIT('Opening telnet connection to {}:{}\n'.format(FICS_HOST, FICS_PORT))
    try:
        # login
        TN = telnetlib.Telnet(FICS_HOST, FICS_PORT)
        EMIT(TN.read_until('login:', TIMEOUT))
        TN.write('guest\n')
        match_index, match, text = TN.expect(['Press return to enter the server as.*$'], TIMEOUT)
        assert (match_index == 0)
        EMIT(text); TN.write('\n\n'); sio.emit('ficsup', {'data': True})
        [app.command_queue.put(cmd) for cmd in PRELIMINARY_COMMANDS]
        CONFIGURED = True; print 'reader configured.'

        while 1:
            try:
                if lock.acquire(blocking=False):
                    output = TN.read_until('fics% ').strip()
                    if len(output):
                        lines = output.split('\n\r')
                        lines = lines[:-1] # prompt is always last, so omit it
                        if len(lines):
                            if is_style12(lines[0]):
                                print lines[0]
                                s12 = parse_style12(lines[0])
                                orientation = 'white'
                                if s12['flip_field'] == 1: orientation = 'black'
                                sio.emit('fen', {'data' :
                                                 fen_from_style12(s12),
                                                 'orientation' : 'white' or orientation
                                                 } )
                            else:
                                [EMIT('{}\n'.format(line)) for line in lines]
            finally:
                lock.release()
    except:
        EMIT(format_exc())
        TN.close()

def fics_w(lock):
        global TN, CONFIGURED
        while not CONFIGURED:
            sleep(1)
        while 1:
            # If we have any data, send it:
            try:
                if lock.acquire(0):
                    command = app.command_queue.get()
                    clog("got cmd: {}".format(command))
                    EMIT(TN.write("{}\n".format(command)))
            except Empty:
                pass
            finally:
                lock.release()
