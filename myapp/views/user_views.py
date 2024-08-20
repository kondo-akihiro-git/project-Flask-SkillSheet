from imports import *
from run import *

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

####################################################################################################
# 
# 関数名：confirm
# 引数：なし
# 返却値：リダイレクト
# 詳細：ユーザーのロ
# 
####################################################################################################

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