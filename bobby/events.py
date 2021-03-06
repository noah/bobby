from threading import Thread, Lock

from flask.ext.socketio import emit as bare_emit

from bobby import sio, app, curry_emit
from remote import fics_r, fics_w
from logger import slog # , clog, log

sock_lock   = None
emit        = curry_emit(bare_emit)('message')

# each one of the following corresponds to client event

@sio.on('connect')
def handle_connected():
    slog('Client connected')
    emit('Connected to web socket server.\n')
    global sock_lock
    if sock_lock is None:
        sock_lock = Lock()
        reader = Thread(target=fics_r, args=(sock_lock,)); reader.daemon = True; reader.start()
        writer = Thread(target=fics_w, args=(sock_lock,)); writer.daemon = True; writer.start()
        slog('started reader and writer')

@sio.on('command')
def handle_command(command):
    slog('`{}\''.format(command['data']))
    app.command_queue.put(command['data'])
