from flask import render_template, Blueprint

mod = Blueprint('bobby', __name__, url_prefix='/')

@mod.route('/')
def index():
    return render_template('home.html')
