import telnetlib
from time import sleep
from traceback import format_exc
from Queue import Empty

from bobby import app, sio, curry_emit
from config import FICS_HOST, FICS_PORT
from logger import clog # , slog, log

from bobby.servers.fics import PRELIMINARY_COMMANDS
from bobby.servers.fics import is_style12, is_g1, s12_state, g1_state,\
                                is_game_state, game_state

#
EMIT                    = curry_emit(sio.emit)
TN                      = None
CONFIGURED              = False
TIMEOUT                 = 3

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
                        # print lines
                        lines = lines[:-1] # prompt is always last, so omit it
                        if len(lines):
                            for line in lines:
                                if is_style12(line):
                                    sio.emit('board-state', { 'data' : s12_state(line) } )
                                elif is_g1(line):
                                    sio.emit('board-state', { 'data' : g1_state(line) } )
                                elif is_game_state(line):
                                    sio.emit('game-state', { 'data' : game_state(line) } )
                                else:
                                    EMIT('{}\n'.format(line))
            finally:
                lock.release()
    except:
        EMIT(format_exc())
        sio.emit('disconnect')
        TN.close()
    print 'end of r'

def fics_w(lock):
        global TN, CONFIGURED
        while not CONFIGURED: sleep(1)
        while 1:
            # If we have any data, send it:
            try:
                if lock.acquire(0):
                    command = app.command_queue.get()
                    clog("got cmd: {}".format(command))
                    EMIT(TN.write("{}\n".format(command)))
                    if(command.lower() == 'quit'): break
            except Empty:
                pass
            finally:
                lock.release()
        print 'end of w'
