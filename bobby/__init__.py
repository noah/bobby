from Queue import Queue

from flask import Flask
from flask.ext.socketio import SocketIO

sio                         = SocketIO()
app                         = Flask(__name__)
app.debug                   = False
app.config['SECRET_KEY']    = 'eicu5jichab5aQuooshohrahghaekajaekahgayaequ0Aix7IHaigh3auphaeCh5'
app.command_queue           = Queue()
#
sio.init_app(app)

curry_emit = lambda emitter: lambda key: lambda data: \
    data is not None and emitter(key, {'data': data})

import events
from bobby.routes import mod; app.register_blueprint(mod)
