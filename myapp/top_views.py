from imports import *
from run import *

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

        # 経験した技術の取得
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        tech_data = {tech_type: {} for tech_type in tech_types}

        for tech_type in tech_types:
            index = 0
            while f'{tech_type}_{index}' in request.form:
                tech_name = request.form[f'{tech_type}_{index}']
                tech_duration = request.form.get(f'{tech_type}_{index}_num', '0')

                if tech_name:
                    if tech_name in tech_data[tech_type]:
                        flash(f'同じプロジェクト内で「{tech_type}」カテゴリーの技術名が重複しています。', 'error')
                        return redirect(url_for('input'))

                    tech_data[tech_type][tech_name] = tech_duration
                index += 1

        # プロジェクトの作成
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
        for tech_type in tech_types:
            for name, duration in tech_data[tech_type].items():
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
# 関数名：feature
# 引数：なし
# 返却値：features.html
# 詳細：SkillCanvasアプリについて説明する
# 
####################################################################################################
@app.route('/features')
def features():
    app.logger.info('Feature page accessed')
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
        app.logger.info('Contact form submitted')
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
    app.logger.info('Contact page accessed')
    return render_template('contact.html')