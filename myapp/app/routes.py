from flask import Blueprint, render_template

main = Blueprint('main', __name__)

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    return render_template('register.html')