from imports import *
from run import *

####################################################################################################
# 
# 関数名：load_user
# 引数：user_id（ユーザーID）
# 返却値：User オブジェクト
# 詳細：ユーザーIDに基づいてユーザーをロードする
# 
####################################################################################################
@login_manager.user_loader # type: ignore
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
@app.route('/') # type: ignore
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
@app.route('/login', methods=['GET', 'POST']) # type: ignore
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first() # type: ignore

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


####################################################################################################
# 
# 関数名：forgot_password
# 引数：なし
# 返却値：forgot_password.html テンプレートまたはリダイレクト
# 詳細：ユーザーのログイン処理を行う
# 
####################################################################################################
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

####################################################################################################
# 
# 関数名：reset_password
# 引数：token
# 返却値：reset_password テンプレートまたはリダイレクト
# 詳細：ユーザーのパスワードリセットを扱います。
# 
####################################################################################################
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
