from flask import render_template, Blueprint, request

mod = Blueprint('bobby', __name__, url_prefix='/bobby')

@mod.route('/')
def index():
    return render_template('home.html')
