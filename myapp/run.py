from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from flask_migrate import Migrate
from flask import jsonify
import uuid

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
# 中間テーブル定義
user_project = db.Table('user_project',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True)
)

class User(db.Model, UserMixin):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    projects = db.relationship('Project', backref='user', lazy=True)
    # 新しいフィールド
    display_name = db.Column(db.String(120), nullable=True)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
    nearest_station = db.Column(db.String(120), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    education = db.Column(db.String(120), nullable=True)

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


class Technology(db.Model):
    __tablename__ = "technology"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    type = db.Column(db.String(120), nullable=False)  # e.g., 'OS', 'language', 'process', etc.
    name = db.Column(db.String(120), nullable=False)
    duration_months = db.Column(db.Integer, nullable=True)  # Nullable for process entries

class Process(db.Model):
    __tablename__ = "process"
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)

class Link(db.Model):
    __tablename__ = 'link'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    link_code = db.Column(db.String(36), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    user = db.relationship('User', backref='links', lazy=True)

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

@app.route('/userinfo', methods=['GET', 'POST'])
@login_required
def userinfo():
    return render_template('userinfo.html', user=current_user)

@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
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
        return redirect(url_for('account'))
    return render_template('account.html', user=current_user)

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

        db.session.commit()
        flash('アカウント情報の更新を完了しました。', 'success')

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

@app.route('/input', methods=['GET', 'POST'])
@login_required
def input():
    if request.method == 'POST':
        start_month_str = request.form['start_month']
        end_month_str = request.form['end_month']
        start_month = start_month_str[:7]  # YYYY-MM形式の文字列に変換
        end_month = end_month_str[:7]      # YYYY-MM形式の文字列に変換
        
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
        db.session.commit()

        # 経験した技術のDB登録
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        for tech_type in tech_types:
            tech_names = [request.form.get(f'{tech_type}_{i}') for i in range(0, len(request.form) + 1) if f'{tech_type}_{i}' in request.form]
            tech_durations = [request.form.get(f'{tech_type}_{i}_num') for i in range(0, len(request.form) + 1) if f'{tech_type}_{i}_num' in request.form]
            for name, duration in zip(tech_names, tech_durations):
                if name:
                    new_technology = Technology(
                        project_id=new_project.id,
                        type=tech_type,
                        name=name,
                        duration_months=int(duration)
                    )
                    db.session.add(new_technology)

        # 担当した工程のDB登録
        processes = request.form.getlist('process')
        for process in processes:
            new_process = Process(
                project_id=new_project.id,
                name=process
            )
            db.session.add(new_process)


        db.session.commit()

        flash('Project and related information successfully added!', 'success')
        return redirect(url_for('index'))

    return render_template('input.html', user=current_user)

@app.route('/sheet', methods=['GET', 'POST'])
@login_required
def sheet():
    user_id = current_user.id
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
    
    return render_template('sheet.html', user=current_user, projects=project_data)

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

@app.route('/edit_project/<int:project_id>', methods=['GET', 'POST'])
@login_required
def edit_project(project_id):
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
            tech_names = [request.form.get(f'{tech_type}_{i}') for i in range(0, len(request.form)) if f'{tech_type}_{i}' in request.form]
            tech_durations = [request.form.get(f'{tech_type}_{i}_num') for i in range(0, len(request.form)) if f'{tech_type}_{i}_num' in request.form]
            existing_techs = Technology.query.filter_by(project_id=project.id, type=tech_type).all()
            existing_names = {tech.name for tech in existing_techs}

            for name, duration in zip(tech_names, tech_durations):
                if name:
                    if duration.isdigit() and int(duration) > 0:
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

            # 空白にされた技術を削除する処理
            for tech in existing_techs:
                if tech.name not in tech_names or not tech.name:
                    db.session.delete(tech)

        # 担当工程の処理
        selected_processes = request.form.getlist('process')
        existing_processes = Process.query.filter_by(project_id=project.id).all()
        existing_names = {process.name for process in existing_processes}
        for process in selected_processes:
            if process not in existing_names:
                new_process = Process(
                    project_id=project.id,
                    name=process
                )
                db.session.add(new_process)

        # 既存のプロセスを削除
        for process in existing_processes:
            if process.name not in selected_processes:
                db.session.delete(process)

        db.session.commit()
        flash('Project updated successfully!', 'success')
        return redirect(url_for('sheet'))

    # プロジェクトの技術と担当工程を取得
    technologies = {tech_type: [] for tech_type in ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']}
    for tech in Technology.query.filter_by(project_id=project_id).all():
        technologies[tech.type].append(tech)

    processes = [process.name for process in Process.query.filter_by(project_id=project_id).all()]

    return render_template('edit_project.html', project=project, technologies=technologies, processes=processes)

@app.route('/create_link', methods=['POST'])
@login_required
def create_link():
    # 現在のユーザーの既存のアクティブリンクをすべて無効化
    Link.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    db.session.commit()

    new_link = Link(
        user_id=current_user.id,
        link_code=str(uuid.uuid4()),
        is_active=True
    )
    db.session.add(new_link)
    db.session.commit()

    # 新しいリンクをフラッシュメッセージとともに返す
    flash('新しいリンクが作成されました。', 'success')
    return jsonify({'link': url_for('view_sheet', link_code=new_link.link_code)})


@app.route('/view_sheet/<link_code>', methods=['GET'])
def view_sheet(link_code):
    # リンクコードに対応するリンクを取得
    link = Link.query.filter_by(link_code=link_code, is_active=True).first()
    if link is None:
        flash('無効なリンクです。', 'error')
        return redirect(url_for('index'))

    # リンクが有効な場合、スキルシートを表示
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

    return render_template('sheet_view.html', user=user, projects=project_data)

@app.route('/invalidate_link', methods=['POST'])
@login_required
def invalidate_link():
    # 現在のユーザーのアクティブなリンクをすべて無効化
    Link.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    db.session.commit()

    flash('リンクが無効化されました。', 'success')
    return redirect(url_for('sheet'))


if __name__ == "__main__":
    app.run(debug=True)


