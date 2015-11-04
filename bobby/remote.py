from traceback import format_exc
import telnetlib
from Queue import Empty

from bobby import app, sio, curry_emit
from config import FICS_HOST, FICS_PORT
from logger import clog, slog, log

first_connect = True

PRELIMINARY_COMMANDS = [
    'set seek 0',
    'set style 12',
]

def fics():
    def style12(s):
        print "`{}'".format(s[:4])
        return s[:4] == '<12>'

    def parse12(s):
        keys = """\
        s12
        row1
        row2
        row3
        row4
        row5
        row6
        row7
        row8
        turn_color
        double_push_file
        white_castle_short
        white_castle_long
        black_castle_short
        black_castle_long
        moves_since_irreversible
        game_number
        white_name
        black_name
        my_relation
        initial_time_secs
        increment_time_secs
        white_strength
        black_strength
        white_time_remain
        black_time_remain
        next_move_number
        coordinate_notation
        previous_move_time
        pretty_notation_previous
        flip_field
        """
        return zip(keys.split(), s.split(' '))


    #
    global first_connect
    TIMEOUT = 3
    emit    = curry_emit(sio.emit)
    emit('Opening connection to freechess.org\n')
    try:
        slog('Opening telnet')
        tn = telnetlib.Telnet(FICS_HOST, FICS_PORT)

        emit(tn.read_until('login:', TIMEOUT))
        # try login as guest
        # https://docs.python.org/2/library/telnetlib.html#telnetlib.Telnet.expect
        tn.write('guest\n')
        match_index, match, text = tn.expect(['Press return to enter the server as.*$'], TIMEOUT)
        if match_index == 0: # matched
            emit(text)
            tn.write('\n\n')
            while True:
                # send telnet output to web client
                output = tn.read_until('fics%', TIMEOUT)
                style12(output)
                #    board = parse12(output)
                #    print board
                #    emit(output)
                # send preliminary (configuration) packets
                if first_connect:
                    [emit(tn.write("{}\n".format(cmd))) for cmd in PRELIMINARY_COMMANDS]
                    first_connect = False
                # send web commands to telnet
                try:
                    command = app.command_queue.get_nowait() # don't block
                    clog("{}".format(command))
                    emit(tn.write("{}\n".format(command)))
                except Empty:
                    pass
    except:
        emit(format_exc())
        tn.close()
        return False
