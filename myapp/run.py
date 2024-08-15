# ライブラリ群のインポート
from imports import *

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

####################################################################################################
# 
# モデル：Form
# 詳細：管理者ログイン時のフォームを扱います。
# 
####################################################################################################
class AdminLoginForm(FlaskForm):
    username = StringField('ユーザー名', validators=[DataRequired()])
    password = PasswordField('パスワード', validators=[DataRequired()])
    submit = SubmitField('ログイン')

from login_views import *

from top_views import *

from sheet_views import *

from admin_views import *


####################################################################################################
# 
# 関数名：メインの実行メソッド
# 
####################################################################################################

if __name__ == "__main__":
    app.run(debug=True)
