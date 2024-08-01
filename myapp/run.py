from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate

# Flaskアプリのインスタンス
app = Flask(__name__)

# セッションのための秘密鍵
app.secret_key = 'your_secret_key'  

# DBのURL
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///flask.db'

# DB操作のための変数
db = SQLAlchemy(app)

# マイグレーションのための変数
migrate = Migrate(app, db)

# ログイン管理のための変数
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# モデルの定義
class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html', user=current_user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful. You can now log in.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if new_username:
            current_user.username = new_username
        if new_password:
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            current_user.password = hashed_password
            db.session.commit()
            flash('Profile updated successfully.', 'success')
        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)

@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    user = User.query.get(current_user.id)
    if user:
        logout_user()
        db.session.delete(user)
        db.session.commit()
        flash('Your account has been deleted.', 'info')
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(debug=True)
