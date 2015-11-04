from threading import Thread

from flask.ext.socketio import emit as bare_emit

from bobby import sio, app, curry_emit
from remote import fics
from logger import clog, slog, log

connection  = None
emit        = curry_emit(bare_emit)

# each one of the following corresponds to client event

@sio.on('connect')
def handle_connected():
    slog('Client connected')
    emit('Websocket connection established.\n')
    global connection
    if connection is None:
        connection = Thread(target=fics)
        connection.start()
        slog('started thread')

@sio.on('command')
def handle_command(command):
    slog('`{}\''.format(command['data']))
    app.command_queue.put(command['data'])
