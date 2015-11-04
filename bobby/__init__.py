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

def curry_emit(f):
    return lambda x: x is not None and f('message', {'data': x.replace('\r','')})

#
import events
from bobby.routes import mod; app.register_blueprint(mod)
