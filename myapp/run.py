from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from flask import jsonify
import uuid
from flask import abort
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired
import yaml
from flask import send_file
from pdf_utils import generate_pdf
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime, timedelta
import re
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer


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

# YAMLファイルの読み込み
# with open('config.yml', 'r') as file:
#     config = yaml.safe_load(file)
# ログディレクトリの作成
if not os.path.exists('logs'):
    os.mkdir('logs')

# ロガーの設定
file_handler = RotatingFileHandler('logs/skill_canvas.log', maxBytes=10240, backupCount=10)
file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
file_handler.setLevel(logging.INFO)

# Flaskアプリケーションのロガーにハンドラーを追加
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# アプリケーション起動時のログ
app.logger.info('SkillCanvas startup')


# Flask-Mailの設定
app.config['MAIL_SERVER'] = 'localhost'
app.config['MAIL_PORT'] = 1025
mail = Mail(app)


# パスワードリセット用のシリアライザ
serializer = URLSafeTimedSerializer(app.secret_key)

####################################################################################################
# 
# 変数：中間テーブル
# 詳細：ユーザーIDとプロジェクトIDを紐付けています。
# 
####################################################################################################
user_project = db.Table('user_project',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

####################################################################################################
# 
# モデル：User
# 詳細：ユーザーの認証関連データとスキルシートに表示するデータを扱います。
# 
####################################################################################################

class User(db.Model, UserMixin):
    __tablename__ = "user"
    # 認証関連のデータ
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_active = db.Column(db.Boolean, default=False) 
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    is_admin = db.Column(db.Boolean, default=False)  # 管理者フラグ
    projects = db.relationship('Project', backref='user', lazy=True)
    # スキルシートに表示するデータ
    display_name = db.Column(db.String(120), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    nearest_station = db.Column(db.String(120), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    education = db.Column(db.String(120), nullable=True)

    def check_password(self, password):
        return check_password_hash(self.password, password)

####################################################################################################
# 
# モデル：Project
# 詳細：参画した案件情報を扱います。
# 
####################################################################################################

class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    start_month = db.Column(db.String(7), nullable=False)  # YYYY-MM形式の文字列
    end_month = db.Column(db.String(7), nullable=False)    # YYYY-MM形式の文字列
    industry = db.Column(db.String(120), nullable=False)
    project_name = db.Column(db.String(120), nullable=False)
    project_summary = db.Column(db.Text, nullable=False)
    responsibilities = db.Column(db.Text, nullable=False)
    technologies = db.relationship('Technology', backref='project', lazy=True)
    processes = db.relationship('Process', backref='project', lazy=True)

####################################################################################################
# 
# モデル：Technology
# 詳細：参画した案件で使用した技術スキルを扱います。
# 
####################################################################################################

class Technology(db.Model):
    __tablename__ = "technology"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    type = db.Column(db.String(120), nullable=False)  # e.g., 'OS', 'language', 'process', etc.
    name = db.Column(db.String(120), nullable=False)
    duration_months = db.Column(db.Integer, nullable=True)  # Nullable for process entries


####################################################################################################
# 
# モデル：Process
# 詳細：参画した案件における担当した開発工程を扱います。
# 
####################################################################################################

class Process(db.Model):
    __tablename__ = "process"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)

####################################################################################################
# 
# モデル：Link
# 詳細：案件面談の際に共有するリンク情報を扱います。
# 
####################################################################################################
class Link(db.Model):
    __tablename__ = 'link'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_code = db.Column(db.String(36), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    user = db.relationship('User', backref='links', lazy=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

####################################################################################################
# 
# モデル：Contact
# 詳細：問い合わせ情報を扱います。
# 
####################################################################################################
# Contactモデル
class Contact(db.Model):
    __tablename__ = 'contact'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)



class AdminLoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')






####################################################################################################
# 
# 関数名：load_user
# 引数：user_id（ユーザーID）
# 返却値：User オブジェクト
# 詳細：ユーザーIDに基づいてユーザーをロードする
# 
####################################################################################################
@login_manager.user_loader
def load_user(user_id):
    # print("管理者ユーザーが追加されました。")
    return User.query.get(int(user_id))

####################################################################################################
# 
# 関数名：index
# 引数：なし
# 返却値：index.html テンプレート
# 詳細：ホームページを表示する
# 
####################################################################################################

@app.route('/')
def index():
    return render_template('index.html', user=current_user)

####################################################################################################
# 
# 関数名：login
# 引数：なし
# 返却値：login.html テンプレートまたはリダイレクト
# 詳細：ユーザーのログイン処理を行う
# 
####################################################################################################
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('Account not confirmed. Please check your email.', 'warning')
                return redirect(url_for('login'))

            login_user(user)
            app.logger.info(f'User {username} logged in successfully.')
            return redirect(url_for('index'))
        
        app.logger.warning(f'Failed login attempt for username: {username}')
        flash('Invalid username or password', 'danger')

    return render_template('login.html')




@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='password-reset-salt')
            reset_url = url_for('reset_password', token=token, _external=True)
            msg = Message('Password Reset Request', sender='noreply@yourapp.com', recipients=[user.email])
            msg.body = f'Please click the following link to reset your password: {reset_url}'
            mail.send(msg)
            flash('A password reset link has been sent to your email.', 'info')
        else:
            flash('Email not found', 'warning')
    return render_template('forgot_password.html')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='password-reset-salt', max_age=3600)
    except:
        flash('The reset link is invalid or has expired.', 'danger')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(password, method='pbkdf2:sha256')
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('login'))
        else:
            flash('User not found', 'danger')
            return redirect(url_for('forgot_password'))

    return render_template('reset_password.html', token=token)

####################################################################################################
# 
# 関数名：register
# 引数：なし
# 返却値：register.html テンプレートまたはリダイレクト
# 詳細：新規ユーザーの登録処理を行う
# 
####################################################################################################
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'], method='pbkdf2:sha256')

        # 新しいユーザーを作成（まだアクティブ化されていない）
        new_user = User(username=username, email=email, password=password, is_active=False)
        db.session.add(new_user)
        db.session.commit()

        # 承認トークンの生成
        token = serializer.dumps(email, salt='email-confirm-salt')
        confirm_url = url_for('confirm_email', token=token, _external=True)

        # 承認メールの送信
        msg = Message('Please confirm your email', sender='noreply@yourapp.com', recipients=[email])
        msg.body = f'Please click the following link to confirm your email: {confirm_url}'
        mail.send(msg)

        flash('A confirmation email has been sent to your email address.', 'info')
        return redirect(url_for('login'))
    
    return render_template('register.html')



@app.route('/confirm_email/<token>')
def confirm_email(token):
    try:
        email = serializer.loads(token, salt='email-confirm-salt', max_age=3600)
    except:
        flash('The confirmation link is invalid or has expired.', 'danger')
        return redirect(url_for('register'))

    user = User.query.filter_by(email=email).first()
    if user.is_active:
        flash('Account already confirmed. Please log in.', 'success')
    else:
        user.is_active = True
        db.session.commit()
        flash('Your account has been confirmed. You can now log in.', 'success')
    
    return redirect(url_for('login'))

####################################################################################################
# 
# 関数名：logout
# 引数：なし
# 返却値：リダイレクト
# 詳細：ユーザーのログアウト処理を行う
# 
####################################################################################################
@app.route('/logout')
@login_required
def logout():
    app.logger.info(f'User {current_user.username} logged out successfully.')
    logout_user()
    return redirect(url_for('index'))

####################################################################################################
# 
# 関数名：userinfo
# 引数：なし
# 返却値：userinfo.html テンプレート
# 詳細：ユーザー情報を表示する
# 
####################################################################################################
@app.route('/userinfo', methods=['GET', 'POST'])
@login_required
def userinfo():
    return render_template('userinfo.html', user=current_user)

####################################################################################################
# 
# 関数名：account
# 引数：なし
# 返却値：account.html テンプレートまたはリダイレクト
# 詳細：ユーザーのアカウント情報を表示および更新する
# 
####################################################################################################
@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    if request.method == 'POST':
        new_username = request.form['username']
        new_email = request.form['email']
        new_password = request.form['password']
        
        # ユーザー名の更新
        if new_username:
            current_user.username = new_username
        
        # メールアドレスの更新
        if new_email:
            current_user.email = new_email
        
        # パスワードの更新
        if new_password:
            hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
            current_user.password = hashed_password
        
        if new_email:
            existing_user = User.query.filter_by(email=new_email).first()
        if existing_user and existing_user.id != current_user.id:
            flash('このメールアドレスは既に使用されています。', 'danger')
        else:
            current_user.email = new_email

        try:
            db.session.commit()
            app.logger.info(f'User account updated for user ID: {current_user.id}')
            flash('アカウント情報を更新しました。', 'success')
        except Exception as e:
            app.logger.error(f'Error updating user account for user ID: {current_user.id} - {str(e)}')
            flash('アカウント情報の更新中にエラーが発生しました。', 'danger')
        
        return redirect(url_for('account'))
    
    return render_template('account.html', user=current_user)


####################################################################################################
# 
# 関数名：profile
# 引数：なし
# 返却値：profile.html テンプレートまたはリダイレクト
# 詳細：スキルシートに表示するユーザーのプロフィール情報を更新する
# 
####################################################################################################
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        new_display_name = request.form['display_name']
        new_age = request.form['age']
        new_gender = request.form['gender']
        new_nearest_station = request.form['nearest_station']
        new_experience_years = request.form['experience_years']
        new_education = request.form['education']

        current_user.display_name = new_display_name
        current_user.age = new_age
        current_user.gender = new_gender
        current_user.nearest_station = new_nearest_station
        current_user.experience_years = new_experience_years
        current_user.education = new_education

        try:
            db.session.commit()
            app.logger.info(f'Profile updated for user ID: {current_user.id}')
            flash('アカウント情報の更新を完了しました。', 'success')
        except Exception as e:
            app.logger.error(f'Error updating profile for user ID: {current_user.id} - {str(e)}')


        return redirect(url_for('profile'))
    return render_template('profile.html', user=current_user)

####################################################################################################
# 
# 関数名：delete_user
# 引数：なし
# 返却値：リダイレクト
# 詳細：ユーザーのアカウントを削除する
# 
####################################################################################################
@app.route('/delete_user', methods=['POST'])
@login_required
def delete_user():
    user = User.query.get(current_user.id)
    if user:
        try:
            logout_user()
            db.session.delete(user)
            db.session.commit()
            app.logger.info(f'User account deleted for user ID: {current_user.id}')
            flash('Your account has been deleted.', 'info')
        except Exception as e:
            app.logger.error(f'Error deleting user account for user ID: {current_user.id} - {str(e)}')
    return redirect(url_for('index'))

####################################################################################################
# 
# 関数名：input
# 引数：なし
# 返却値：input.html テンプレートまたはリダイレクト
# 詳細：新しいプロジェクトを入力し、データベースに追加する
# 
####################################################################################################
@app.route('/input', methods=['GET', 'POST'])
@login_required
def input():
    if request.method == 'POST':
        start_month_str = request.form['start_month']
        end_month_str = request.form['end_month']
        start_month = start_month_str[:7]
        end_month = end_month_str[:7]

        industry = request.form['industry']
        project_name = request.form['project_name']
        project_summary = request.form['project_summary']
        responsibilities = request.form['responsibilities']

        new_project = Project(
            user_id=current_user.id,
            start_month=start_month,
            end_month=end_month,
            industry=industry,
            project_name=project_name,
            project_summary=project_summary,
            responsibilities=responsibilities
        )

        db.session.add(new_project)
        try:
            db.session.commit()
            app.logger.info(f'New project added for user ID: {current_user.id}')
        except Exception as e:
            app.logger.error(f'Error adding project for user ID: {current_user.id} - {str(e)}')

        # 経験した技術のDB登録
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        for tech_type in tech_types:
            tech_names = []
            tech_durations = []
            index = 0
            while f'{tech_type}_{index}' in request.form:
                tech_name = request.form[f'{tech_type}_{index}']
                tech_duration = request.form.get(f'{tech_type}_{index}_num', '0')

                # 技術名が入力されている場合、期間が未入力なら0を設定
                if tech_name and not tech_duration:
                    tech_duration = '0'

                tech_names.append(tech_name)
                tech_durations.append(tech_duration)
                index += 1

            for name, duration in zip(tech_names, tech_durations):
                if name:
                    new_technology = Technology(
                        project_id=new_project.id,
                        type=tech_type,
                        name=name,
                        duration_months=int(duration)
                    )
                    db.session.add(new_technology)

        try:
            db.session.commit()
            app.logger.info(f'Technologies added for project ID: {new_project.id}')
        except Exception as e:
            app.logger.error(f'Error adding technologies for project ID: {new_project.id} - {str(e)}')

        # 担当した工程のDB登録
        processes = request.form.getlist('process')
        for process in processes:
            new_process = Process(
                project_id=new_project.id,
                name=process
            )
            db.session.add(new_process)

        try:
            db.session.commit()
            app.logger.info(f'Processes added for project ID: {new_project.id}')
        except Exception as e:
            app.logger.error(f'Error adding processes for project ID: {new_project.id} - {str(e)}')

        flash('プロジェクトを追加しました。', 'success')
        return redirect(url_for('input'))

    return render_template('input.html', user=current_user)



####################################################################################################
# 
# 関数名：sheet
# 引数：なし
# 返却値：sheet.html テンプレート
# 詳細：ユーザーのプロジェクトと関連情報を表示する
# 
####################################################################################################
@app.route('/sheet', methods=['GET', 'POST'])
@login_required
def sheet():
    user_id = current_user.id
    projects = Project.query.filter_by(user_id=user_id).all()
    project_data = []
    skills_by_category = {}

    tech_type_mapping = {
        'os': 'OS',
        'language': '言語',
        'framework': 'フレームワーク',
        'database': 'データベース',
        'containertech': 'コンテナ技術',
        'cicd': 'CI/CD',
        'logging': 'ログ',
        'tools': 'その他ツール'
    }

    for project in projects:
        processes = Process.query.filter_by(project_id=project.id).all()
        technologies = Technology.query.filter_by(project_id=project.id).all()
        
        for tech in technologies:
            tech_type = tech_type_mapping[tech.type]
            if tech_type not in skills_by_category:
                skills_by_category[tech_type] = {}
            
            if tech.name not in skills_by_category[tech_type]:
                skills_by_category[tech_type][tech.name] = tech.duration_months
            else:
                skills_by_category[tech_type][tech.name] += tech.duration_months
        
        project_data.append({
            'project': project,
            'processes': processes,
            'technologies': technologies
        })

    skills_by_category_formatted = {}
    for category, skills in skills_by_category.items():
        skills_list = [{'name': name, 'duration_months': duration} for name, duration in skills.items()]
        skills_by_category_formatted[category] = skills_list

    # 最新のアクティブなリンクを取得
    active_link = Link.query.filter_by(user_id=user_id, is_active=True).order_by(Link.created_at.desc()).first()

    link_url = url_for('view_sheet', link_code=active_link.link_code, _external=True) if active_link else None

    # `user.experience_years` が None の場合に備えてデフォルト値を設定
    experience_years = current_user.experience_years or 0

    return render_template('sheet.html', user=current_user, projects=project_data, skills_by_category=skills_by_category_formatted, tech_type_mapping=tech_type_mapping, link_url=link_url, experience_years=experience_years)

####################################################################################################
# 
# 関数名：edit_profile
# 引数：なし
# 返却値：edit_profile.html テンプレートまたはリダイレクト
# 詳細：スキルシート上からユーザーのプロフィール情報を編集する
# 
####################################################################################################
@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        current_user.display_name = request.form['display_name']
        current_user.age = request.form['age']
        current_user.gender = request.form['gender']
        current_user.nearest_station = request.form['nearest_station']
        current_user.experience_years = request.form['experience_years']
        current_user.education = request.form['education']
        db.session.commit()
        flash('プロフィール情報が更新されました。', 'success')
        return redirect(url_for('sheet'))
    return render_template('edit_profile.html', user=current_user)

####################################################################################################
# 
# 関数名：edit_project
# 引数：project_id（プロジェクトID）
# 返却値：edit_project.html テンプレートまたはリダイレクト
# 詳細：指定したプロジェクトの情報を編集する
# 
####################################################################################################
@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
    project = Project.query.get_or_404(project_id)
    
    tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']

    if request.method == 'POST':
        # プロジェクトの基本情報を更新
        project.project_name = request.form['project_name']
        project.industry = request.form['industry']
        project.start_month = request.form['start_month']
        project.end_month = request.form['end_month']
        project.project_summary = request.form['project_summary']
        project.responsibilities = request.form['responsibilities']

        # 技術の処理
        for tech_type in tech_types:
            tech_names = [request.form.get(f'{tech_type}_{i}') for i in range(len(request.form)) if f'{tech_type}_{i}' in request.form]
            tech_durations = [request.form.get(f'{tech_type}_{i}_num') for i in range(len(request.form)) if f'{tech_type}_{i}_num' in request.form]
            existing_techs = Technology.query.filter_by(project_id=project.id, type=tech_type).all()
            existing_names = {tech.name for tech in existing_techs}

            # 新しい技術を追加または更新
            for name, duration in zip(tech_names, tech_durations):
                if name and duration.isdigit() and int(duration) > 0:
                    if name in existing_names:
                        tech = next(tech for tech in existing_techs if tech.name == name)
                        tech.duration_months = int(duration)
                    else:
                        new_technology = Technology(
                            project_id=project.id,
                            type=tech_type,
                            name=name,
                            duration_months=int(duration)
                        )
                        db.session.add(new_technology)
            
            # 削除された技術を特定して削除
            submitted_names = set(tech_names)
            for tech in existing_techs:
                if tech.name not in submitted_names:
                    db.session.delete(tech)
        
        db.session.commit()

        # 担当工程の処理
        selected_processes = request.form.getlist('process')
        existing_processes = Process.query.filter_by(project_id=project.id).all()
        existing_process_names = {process.name for process in existing_processes}

        for process_name in selected_processes:
            if process_name not in existing_process_names:
                new_process = Process(
                    project_id=project.id,
                    name=process_name
                )
                db.session.add(new_process)
        
        for process in existing_processes:
            if process.name not in selected_processes:
                db.session.delete(process)
                
        db.session.commit()

        flash('プロジェクトが更新されました', 'success')
        return redirect(url_for('edit_project', project_id=project.id))

    technologies = {}
    for tech_type in tech_types:
        techs = Technology.query.filter_by(project_id=project.id, type=tech_type).all()
        if not techs:
            techs = [{'name': '', 'duration_months': ''}]  # 空のリストを渡す
        technologies[tech_type] = techs

    processes = [process.name for process in Process.query.filter_by(project_id=project.id).all()]

    return render_template('edit_project.html', project=project, processes=processes, technologies=technologies)

####################################################################################################
# 
# 関数名：create_link
# 引数：なし
# 返却値：JSON（リンクURLを含む）
# 詳細：新しいリンクを作成し、現在のアクティブなリンクを無効化する
# 
####################################################################################################
@app.route('/create_link', methods=['POST'])
@login_required
def create_link():

    new_link = Link(
        user_id=current_user.id,
        link_code=str(uuid.uuid4()),
        is_active=True
    )
    db.session.add(new_link)
    db.session.commit()

    # リンクURLを生成
    link_url = url_for('view_sheet', link_code=new_link.link_code, _external=True)

    return jsonify({'link': link_url})

####################################################################################################
# 
# 関数名：view_sheet
# 引数：link_code
# 返却値：view_sheet.html　（リンクが無効な場合は invalid.html）  
# 詳細：特定のリンクを知っている人だけが閲覧のみの画面を表示でき仕様
# 
####################################################################################################

@app.route('/view_sheet/<link_code>', methods=['GET'])
def view_sheet(link_code):
    # リンクコードに対応するリンクを取得
    link = Link.query.filter_by(link_code=link_code, is_active=True).first()
    if link is None:
        flash('無効なリンクです。', 'error')
        current_url=request.url
        return render_template('invalid.html', current_url=current_url)

    # リンクが有効な場合、スキルシートを表示するためデータを受け渡し
    user_id = link.user_id
    user = User.query.get_or_404(user_id)
    projects = Project.query.filter_by(user_id=user_id).all()
    project_data = []

    for project in projects:
        technologies = Technology.query.filter_by(project_id=project.id).all()
        processes = Process.query.filter_by(project_id=project.id).all()
        project_data.append({
            'project': project,
            'technologies': technologies,
            'processes': processes
        })

    return render_template('view_sheet.html', user=user, projects=project_data,link_code=link_code)

####################################################################################################
# 
# 関数名：invalidate_link
# 引数：なし
# 返却値：sheetにリダイレクト
# 詳細：全てのリンクを無効化する仕様
# 
####################################################################################################

@app.route('/invalidate_link', methods=['POST'])
@login_required
def invalidate_link():
    # 現在のアクティブなリンクを無効化
    Link.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    
    # 現在のユーザーの既存のアクティブリンク以外をすべて削除
    inactive_links = Link.query.filter_by(user_id=current_user.id, is_active=False).all()
    for link in inactive_links:
        db.session.delete(link)
    db.session.commit()

    flash('リンクが無効化されました。', 'success')
    return redirect(url_for('sheet'))

####################################################################################################
# 
# 関数名：delete_project
# 引数：project_id（プロジェクトID）
# 返却値：リダイレクト
# 詳細：指定したプロジェクトを削除する
# 
####################################################################################################
@app.route('/delete_project/<int:project_id>', methods=['POST'])
@login_required
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    if project.user_id == current_user.id:
        db.session.delete(project)
        db.session.commit()
        flash('プロジェクトが削除されました。', 'success')
    else:
        flash('削除できるのは自身のプロジェクトのみです。', 'danger')
    return redirect(url_for('sheet'))

####################################################################################################
# 
# 関数名：feature
# 引数：なし
# 返却値：features.html
# 詳細：SkillCanvasアプリについて説明する
# 
####################################################################################################
@app.route('/features')
def features():
    return render_template('features.html')

####################################################################################################
# 
# 関数名：contact
# 引数：なし
# 返却値：contact.html
# 詳細：お問い合わせを送信する
# 
####################################################################################################
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Process the contact form data
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        # Here you could save the message to the database or send an email

        # Contactオブジェクトの作成と保存
        new_contact = Contact(name=name, email=email, message=message)
        db.session.add(new_contact)
        db.session.commit()

        flash('お問い合わせありがとうございます。こちらからの返信をお待ちください。', 'success')
        return redirect(url_for('contact'))
    return render_template('contact.html')

####################################################################################################
# 
# 関数群：admin
# 詳細：管理者画面における画面遷移、CRUDを担当する
# 
####################################################################################################

# 管理者確認のためのデコレーター
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # アクセス禁止
        return f(*args, **kwargs)
    return decorated_function

# 管理者ログイン
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()  # フォームクラスを定義してください
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_admin:
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('ログイン情報が無効です。', 'danger')
    return render_template('admin_login.html', form=form)

# 管理者ダッシュボード
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

# ログアウト処理
@app.route('/admin/logout')
@login_required
@admin_required
def admin_logout():
    logout_user()
    return redirect(url_for('admin_login'))

# 管理者画面のユーザー一覧表示
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin_users.html', users=users)

# ユーザーの詳細表示および編集
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.email = request.form['email']
        user.display_name = request.form['display_name']
        user.age = request.form['age']
        user.gender = request.form['gender']
        user.nearest_station = request.form['nearest_station']
        user.experience_years = request.form['experience_years']
        user.education = request.form['education']
        user.is_admin = 'is_admin' in request.form 
        db.session.commit()
        flash('ユーザー情報が更新されました。', 'success')
        return redirect(url_for('admin_user_detail', user_id=user.id))

    # 最新の有効なスキルシートのリンクを取得
    latest_active_link = Link.query.filter_by(user_id=user.id, is_active=True).order_by(Link.created_at.desc()).first()
    # リンクコードをフルURLに変換
    if latest_active_link:
        latest_active_link_url = url_for('view_sheet', link_code=latest_active_link.link_code, _external=True)
    else:
        latest_active_link_url = None

    return render_template('admin_user_detail.html', user=user, latest_active_url=latest_active_link_url)


# ユーザーの削除
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('ユーザーが削除されました。', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/projects')
@login_required
@admin_required
def admin_projects():
    # プロジェクトとその関連テクノロジーを取得
    projects = Project.query.all()

    # プロジェクトIDを取得
    project_ids = [project.id for project in projects]

    # プロジェクトに関連するプロセスを取得
    processes = Process.query.filter(Process.project_id.in_(project_ids)).all()

    # プロジェクトIDごとにプロセスをマッピング
    project_processes = {}
    for process in processes:
        if process.project_id not in project_processes:
            project_processes[process.project_id] = []
        project_processes[process.project_id].append(process)

    return render_template('admin_projects.html', projects=projects, project_processes=project_processes)



@app.route('/admin/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_project_detail(project_id):
    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        # プロジェクトの基本情報を更新
        project.project_name = request.form['project_name']
        project.industry = request.form['industry']
        project.start_month = request.form['start_month']
        project.end_month = request.form['end_month']
        project.project_summary = request.form['project_summary']
        project.responsibilities = request.form['responsibilities']

        # 技術の処理
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        for tech_type in tech_types:
            tech_names = []
            tech_durations = []
            i = 0
            while f'{tech_type}_{i}' in request.form:
                tech_name = request.form.get(f'{tech_type}_{i}')
                tech_duration = request.form.get(f'{tech_type}_{i}_num')
                if tech_name:
                    tech_names.append(tech_name)
                    tech_durations.append(tech_duration)
                i += 1

            existing_techs = Technology.query.filter_by(project_id=project.id, type=tech_type).all()
            existing_names = {tech.name for tech in existing_techs}

            for name, duration in zip(tech_names, tech_durations):
                if name and duration.isdigit() and int(duration) > 0:
                    if name in existing_names:
                        tech = next(tech for tech in existing_techs if tech.name == name)
                        tech.duration_months = int(duration)
                    else:
                        new_technology = Technology(
                            project_id=project.id,
                            type=tech_type,
                            name=name,
                            duration_months=int(duration)
                        )
                        db.session.add(new_technology)
                elif name in existing_names:
                    tech = next(tech for tech in existing_techs if tech.name == name)
                    db.session.delete(tech)

            # 空白にする処理を追加
            for tech in existing_techs:
                if tech.name not in tech_names:
                    db.session.delete(tech)

        # 工程の処理
        processes = request.form.getlist('process')
        existing_processes = Process.query.filter_by(project_id=project.id).all()
        existing_names = {process.name for process in existing_processes}

        for process_name in ['要件定義', '基本設計', '詳細設計', '実装', '単体テスト', '結合テスト', '受入テスト', '運用・保守']:
            if process_name in processes:
                if process_name not in existing_names:
                    new_process = Process(project_id=project.id, name=process_name)
                    db.session.add(new_process)
            else:
                if process_name in existing_names:
                    process = next(p for p in existing_processes if p.name == process_name)
                    db.session.delete(process)

        db.session.commit()
        flash('プロジェクトが更新されました。', 'success')
        return redirect(url_for('admin_project_detail', project_id=project_id))

    technologies = {tech_type: Technology.query.filter_by(project_id=project.id, type=tech_type).all() for tech_type in ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']}
    processes = [process.name for process in Process.query.filter_by(project_id=project.id).all()]

    return render_template('admin_project_detail.html', project=project, technologies=technologies, processes=processes)


# プロジェクトの削除
@app.route('/admin/project/delete/<int:project_id>', methods=['POST'])
@login_required
@admin_required
def admin_project_delete(project_id):
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('プロジェクトが削除されました。', 'success')
    return redirect(url_for('admin_projects'))

@app.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_create():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        email = request.form['email']  # メールアドレスの取得
        display_name = request.form.get('display_name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        nearest_station = request.form.get('nearest_station')
        experience_years = request.form.get('experience_years')
        education = request.form.get('education')
        is_admin = 'is_admin' in request.form  # チェックボックスの処理

        new_user = User(
            username=username,
            password=password,
            email=email,  # メールアドレスを設定
            display_name=display_name,
            age=age,
            gender=gender,
            nearest_station=nearest_station,
            experience_years=experience_years,
            education=education,
            is_admin=is_admin
        )
        db.session.add(new_user)
        db.session.commit()
        flash('新規ユーザーが登録されました。', 'success')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_create.html')



@app.route('/admin/users_pagination', methods=['GET'])
@login_required
@admin_required
def admin_users_pagination():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 検索条件の取得
    user_id = request.args.get('user_id')
    username = request.args.get('username')
    email = request.args.get('email')
    display_name = request.args.get('display_name')
    age = request.args.get('age')
    gender = request.args.get('gender')
    nearest_station = request.args.get('nearest_station')
    experience_years = request.args.get('experience_years')
    education = request.args.get('education')
    latest_active_link_url = request.args.get('latest_active_link_url')
    is_admin = request.args.get('is_admin')

    # クエリの作成
    query = User.query

    if user_id:
        query = query.filter(User.id == user_id)
    if username:
        query = query.filter(User.username.like(f'%{username}%'))
    if email:
        query = query.filter(User.email.like(f"%{email}%"))
    if display_name:
        query = query.filter(User.display_name.like(f'%{display_name}%'))
    if age:
        query = query.filter(User.age == age)
    if gender:
        query = query.filter(User.gender.like(f'%{gender}%'))
    if nearest_station:
        query = query.filter(User.nearest_station.like(f'%{nearest_station}%'))
    if experience_years:
        query = query.filter(User.experience_years == experience_years)
    if education:
        query = query.filter(User.education.like(f'%{education}%'))
    if latest_active_link_url:
        subquery = Link.query.filter(Link.link_code.like(f'%{latest_active_link_url}%')).subquery()
        query = query.filter(User.id.in_(db.session.query(Link.user_id).filter(Link.is_active == True).filter(Link.link_code.like(f'%{latest_active_link_url}%')).subquery()))
    if is_admin is not None:
        if is_admin == 'null':
            query = query.filter(User.is_admin.is_(None))
        elif is_admin == 'true':
            query = query.filter(User.is_admin.is_(True))
        elif is_admin == 'false':
            query = query.filter(User.is_admin.is_(False))

    users_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    users = users_paginated.items
    total = users_paginated.total
    pages = users_paginated.pages

    users_data = []
    for user in users:
        latest_active_link = db.session.query(Link).filter_by(user_id=user.id, is_active=True).order_by(Link.created_at.desc()).first()
        latest_active_link_url = url_for('view_sheet', link_code=latest_active_link.link_code, _external=True) if latest_active_link else None

        users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'display_name': user.display_name,
            'age': user.age,
            'gender': user.gender,
            'nearest_station': user.nearest_station,
            'experience_years': user.experience_years,
            'education': user.education,
            'latest_active_link_url': latest_active_link_url,
            'is_admin': user.is_admin,
        })

    return jsonify({
        'users': users_data,
        'total': total,
        'pages': pages,
        'current_page': page
    })

# run.py の一部

@app.route('/create_admin', methods=['POST'])
def create_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        return redirect(url_for('login'))
    
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        admin_user = User(username=username, password=hashed_password, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        flash('Admin user created successfully!')
        return redirect(url_for('admin_dashboard'))
    flash('Failed to create admin user. Please check the form and try again.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/project/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_project_create():
    if request.method == 'POST':
        # ログインユーザーのIDを取得
        user_id = current_user.id
        
        # 新規プロジェクトの作成
        project = Project(
            user_id=user_id,  # user_id を追加
            project_name=request.form['project_name'],
            industry=request.form['industry'],
            start_month=request.form['start_month'],
            end_month=request.form['end_month'],
            project_summary=request.form['project_summary'],
            responsibilities=request.form['responsibilities']
        )
        db.session.add(project)
        db.session.commit()

        # 技術の処理
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        for tech_type in tech_types:
            tech_names = [request.form.get(f'{tech_type}_{i}') for i in range(0, len(request.form)) if f'{tech_type}_{i}' in request.form]
            tech_durations = [request.form.get(f'{tech_type}_{i}_num') for i in range(0, len(request.form)) if f'{tech_type}_{i}_num' in request.form]

            for name, duration in zip(tech_names, tech_durations):
                if name:
                    if duration.isdigit() and int(duration) > 0:
                        new_technology = Technology(
                            project_id=project.id,
                            type=tech_type,
                            name=name,
                            duration_months=int(duration)
                        )
                        db.session.add(new_technology)

        # 工程の処理
        processes = request.form.getlist('process')
        for process_name in ['要件定義', '基本設計', '詳細設計', '実装', '単体テスト', '結合テスト', '受入テスト', '運用・保守']:
            if process_name in processes:
                new_process = Process(
                    project_id=project.id,
                    name=process_name
                )
                db.session.add(new_process)

        db.session.commit()

        flash('プロジェクトが正常に作成されました', 'success')
        return redirect(url_for('admin_dashboard'))

    return render_template('admin_project_create.html')

@app.route('/admin/projects_pagination', methods=['GET'])
@login_required
@admin_required
def admin_projects_pagination():
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # 検索条件の取得
    project_id = request.args.get('project_id')
    project_name = request.args.get('project_name')
    industry = request.args.get('industry')
    start_month = request.args.get('start_month')
    end_month = request.args.get('end_month')
    project_summary = request.args.get('project_summary')
    responsibilities = request.args.get('responsibilities')
    technologies = request.args.get('technologies')
    processes = request.args.get('processes')

    # クエリの作成
    query = Project.query

    if project_id:
        query = query.filter(Project.id == project_id)
    if project_name:
        query = query.filter(Project.project_name.like(f'%{project_name}%'))
    if industry:
        query = query.filter(Project.industry.like(f'%{industry}%'))
    if start_month:
        query = query.filter(Project.start_month >= start_month)
    if end_month:
        query = query.filter(Project.end_month <= end_month)
    if project_summary:
        query = query.filter(Project.project_summary.like(f'%{project_summary}%'))
    if responsibilities:
        query = query.filter(Project.responsibilities.like(f'%{responsibilities}%'))
    if technologies:
        query = query.join(Project.technologies).filter(Technology.name.like(f'%{technologies}%'))
    if processes:
        query = query.join(Project.processes).filter(Process.name.like(f'%{processes}%'))

    projects_paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    projects = projects_paginated.items
    total = projects_paginated.total
    pages = projects_paginated.pages

    projects_data = []
    for project in projects:
        technologies_list = [tech.name for tech in project.technologies]
        processes_list = [proc.name for proc in project.processes]

        projects_data.append({
            'id': project.id,
            'project_name': project.project_name,
            'industry': project.industry,
            'start_month': project.start_month,
            'end_month': project.end_month,
            'project_summary': project.project_summary,
            'responsibilities': project.responsibilities,
            'technologies': technologies_list,
            'processes': processes_list,
        })

    return jsonify({
        'projects': projects_data,
        'total': total,
        'pages': pages,
        'current_page': page
    })



@app.route('/download_pdf/<link_code>', methods=['GET'])
def download_pdf(link_code):
    # リンクコードに対応するリンクを取得
    link = Link.query.filter_by(link_code=link_code, is_active=True).first()
    if link is None:
        flash('無効なリンクです。', 'error')
        return redirect(url_for('invalid'))

    # スキルシートのデータを取得
    user_id = link.user_id
    user = User.query.get_or_404(user_id)
    projects = Project.query.filter_by(user_id=user_id).all()
    project_data = []

    for project in projects:
        technologies = Technology.query.filter_by(project_id=project.id).all()
        processes = Process.query.filter_by(project_id=project.id).all()
        project_data.append({
            'project': project,
            'technologies': technologies,
            'processes': processes
        })

    # PDF生成
    pdf_buffer = generate_pdf(user, project_data)
    return send_file(pdf_buffer, as_attachment=True, download_name='skill_sheet.pdf', mimetype='application/pdf')



@app.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    logs = []
    log_file_path = 'logs/skill_canvas.log'
    
    # 最新の10日分のログを保持するためのリスト
    recent_logs = []
    now = datetime.now()

    try:
        with open(log_file_path, 'r') as log_file:
            for line in log_file:
                # ログのタイムスタンプを抽出してパースする
                try:
                    timestamp_str = line.split()[0] + ' ' + line.split()[1]
                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S,%f')
                except ValueError:
                    continue
                
                # 最新の10日以内のログをリストに追加
                if now - timedelta(days=10) <= timestamp <= now:
                    recent_logs.append(line)
    except FileNotFoundError:
        app.logger.error('Log file not found.')

    # 最新の10日分のログを表示
    return render_template('admin_logs.html', logs=recent_logs)


@app.route('/admin/contacts')
@login_required
@admin_required
def admin_contacts():
    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('admin_contacts.html', contacts=contacts)

@app.route('/admin/contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def reply_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    if request.method == 'POST':
        reply_message = request.form['reply_message']
        # 件名を手動で設定
        msg = Message('Re: お問い合わせについて',
                    sender='your_email@example.com',
                    recipients=[contact.email])
        msg.body = reply_message
        mail.send(msg)
        flash('返信が送信されました。', 'success')
        return redirect(url_for('admin_contacts'))

    return render_template('reply_contact.html', contact=contact)


####################################################################################################
# 
# 関数名：メインの実行メソッド
# 
####################################################################################################

if __name__ == "__main__":
    app.run(debug=True)
