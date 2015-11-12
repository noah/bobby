import telnetlib
from re import match
from time import sleep
from Queue import Empty
from traceback import format_exc
from collections import defaultdict

from bobby import app, sio, curry_emit
from config import FICS_HOST, FICS_PORT
from logger import clog # , slog, log

from bobby.servers.fics import PRELIMINARY_COMMANDS, s12_state, g1_state, game_state

#
EMIT                    = curry_emit(sio.emit)('message')
EMIT_BOARD              = curry_emit(sio.emit)('board-state')
EMIT_GAME               = curry_emit(sio.emit)('game-state')
TN                      = None
CONFIGURED              = False
TIMEOUT                 = 3

def fics_r(lock):
    def process_line(line):
        if match(r'<12>',    line): return EMIT_BOARD, s12_state(line)
        elif match(r'<g1>',  line): return EMIT_BOARD, g1_state(line)
        elif match(r'{Game', line): return EMIT_GAME, game_state(line)
        else:                       return EMIT, line

    global TN, CONFIGURED
    EMIT('Opening telnet connection to {}:{}\n'.format(FICS_HOST, FICS_PORT))
    try:
        # login
        TN = telnetlib.Telnet(FICS_HOST, FICS_PORT)
        EMIT(TN.read_until('login:', TIMEOUT).replace('\r',''))
        TN.write('guest\n')
        match_index, _, text = TN.expect(['Press return to enter the server as.*$'], TIMEOUT)
        assert (match_index == 0)
        EMIT(text); TN.write('\n\n'); sio.emit('ficsup', {'data': True})
        [app.command_queue.put(cmd) for cmd in PRELIMINARY_COMMANDS]
        CONFIGURED = True; print 'reader configured.'
        while TN is not None:
            try:
                if lock.acquire(blocking=False):
                    output = TN.read_until('fics% ').strip()
                    if len(output):
                        # note: emit()ting multiple join()ed lines (messages) to a
                        # single socket handler is ***much*** more performant
                        # than emit()ting once per message (line)!
                        messages = defaultdict(list)
                        for line in output.split('\n\r')[:-1]: # -1: omit prompt line
                            femit, message = process_line(line)
                            messages[femit].append(message)
                        for femit, messages in messages.iteritems():
                            # string type messages
                            if femit in [EMIT]: femit('\n'.join(messages) + '\n')
                            # higher-order type
                            else: [femit(m) for m in messages]
            finally: lock.release()
    except EOFError, e:
        EMIT(str(e))
    except Exception, e:
        EMIT(format_exc())
    finally:
        if TN is not None:
            TN.close()

def fics_w(lock):
    global TN, CONFIGURED
    while not CONFIGURED: sleep(1)
    while TN is not None:
        try: # If we have any data, send it
            if lock.acquire(0):
                command = app.command_queue.get()
                clog("got cmd: {}".format(command))
                EMIT(TN.write("{}\n".format(command)))
                if command.lower() == 'quit':
                    break
        except Empty: pass
        finally: lock.release()
