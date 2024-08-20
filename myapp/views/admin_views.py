from imports import *
from run import *


####################################################################################################
# 
# 関数名：admin_required
# 引数：f (デコレータとして使用する関数)
# 返却値：デコレータ関数
# 詳細：このデコレータは、アクセスするユーザーが管理者であるかを確認します。ユーザーが管理者でない場合、403 Forbidden エラーを返します。
# 
####################################################################################################
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            app.logger.warning(f'Unauthorized access attempt by user {current_user.id}')
            abort(403)  # アクセス禁止
        return f(*args, **kwargs)
    return decorated_function

####################################################################################################
# 
# 関数名：admin_login
# 引数：なし
# 返却値：admin_login.html
# 詳細：管理者ログインページを表示し、ログイン情報を検証します。正しい情報が提供された場合、管理者ダッシュボードにリダイレクトします。
# 
####################################################################################################
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()  # type: ignore # フォームクラスを定義してください
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data) and user.is_admin:
            login_user(user)
            app.logger.info(f'Admin {user.id} logged in')
            return redirect(url_for('admin_dashboard'))
        flash('ログイン情報が無効です。', 'danger')
        app.logger.warning(f'Failed admin login attempt for username: {form.username.data}')
    app.logger.info('Admin login page accessed')
    return render_template('admin_login.html', form=form)

####################################################################################################
# 
# 関数名：admin_dashboard
# 引数：なし
# 返却値：admin_dashboard.html
# 詳細：管理者ダッシュボードページを表示します。アクセスにはログインと管理者権限が必要です。
# 
####################################################################################################
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    app.logger.info(f'Admin {current_user.id} accessed dashboard')
    return render_template('admin_dashboard.html')

####################################################################################################
# 
# 関数名：admin_logout
# 引数：なし
# 返却値：管理者ログインページへのリダイレクト
# 詳細：管理者ログアウト処理を行い、ログアウト後はログインページにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/logout')
@login_required
@admin_required
def admin_logout():
    app.logger.info(f'Admin {current_user.id} logged out')
    logout_user()
    return redirect(url_for('admin_login'))

####################################################################################################
# 
# 関数名：admin_users
# 引数：なし
# 返却値：admin_users.html
# 詳細：全ユーザーの一覧を表示するページを提供します。管理者のログインが必要です。
# 
####################################################################################################
@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    app.logger.info(f'Admin {current_user.id} accessed user list')
    users = User.query.all()
    return render_template('admin_users.html', users=users)

####################################################################################################
# 
# 関数名：admin_user_detail
# 引数：user_id (ユーザーのID)
# 返却値：admin_user_detail.html
# 詳細：指定されたユーザーIDの詳細情報を表示し、情報の更新を行います。また、最新の有効なスキルシートのリンクを取得し、表示します。
# 
####################################################################################################
@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        app.logger.info(f'Admin {current_user.id} updated user {user.id}')
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

    app.logger.info(f'Admin {current_user.id} accessed user detail for user {user.id}')
    return render_template('admin_user_detail.html', user=user, latest_active_url=latest_active_link_url)


####################################################################################################
# 
# 関数名：admin_user_delete
# 引数：user_id (削除するユーザーのID)
# 返却値：管理者ユーザー一覧ページへのリダイレクト
# 詳細：指定されたユーザーIDのユーザーを削除し、削除後はユーザー一覧ページにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/user/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def admin_user_delete(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    app.logger.info(f'Admin {current_user.id} deleted user {user.id}')
    flash('ユーザーが削除されました。', 'success')
    return redirect(url_for('admin_users'))

####################################################################################################
# 
# 関数名：admin_projects
# 引数：なし
# 返却値：admin_projects.html
# 詳細：全プロジェクトとその関連テクノロジーを一覧表示するページを提供します。プロジェクトとプロセスを取得し、表示します。
# 
####################################################################################################
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

    app.logger.info(f'Admin {current_user.id} accessed project list')
    return render_template('admin_projects.html', projects=projects, project_processes=project_processes)

####################################################################################################
# 
# 関数名：admin_project_detail
# 引数：project_id (int) - プロジェクトのID
# 返却値：admin_project_detail.html
# 詳細：指定されたプロジェクトIDに基づいて、プロジェクトの詳細情報とその関連技術、プロセスを表示するページを提供します。フォームからプロジェクトの基本情報と技術、プロセスを更新することができます。
# 
####################################################################################################
@app.route('/admin/project/<int:project_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_project_detail(project_id):
    app.logger.info('Accessing admin_project_detail')

    project = Project.query.get_or_404(project_id)

    if request.method == 'POST':
        app.logger.info(f'Updating project {project_id}')
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

            # 重複チェック
            tech_names_set = set(tech_names)
            if len(tech_names) != len(tech_names_set):
                flash(f'{tech_type.capitalize()} の技術名が重複しています。', 'error')
                app.logger.info(f'Duplicate technology name found in {tech_type}')
                return redirect(url_for('admin_project_detail', project_id=project_id))

            # 既存技術の取得と名前のリスト作成
            existing_techs = Technology.query.filter_by(project_id=project.id, type=tech_type).all()
            existing_names = {tech.name for tech in existing_techs}

            # 更新と新規追加
            for name, duration in zip(tech_names, tech_durations):
                if name and duration.isdigit() and int(duration) > 0:
                    if name in existing_names:
                        tech = next(tech for tech in existing_techs if tech.name == name)
                        tech.duration_months = int(duration)
                        app.logger.info(f'Updated technology {name} in {tech_type}')
                    else:
                        new_technology = Technology(
                            project_id=project.id,
                            type=tech_type,
                            name=name,
                            duration_months=int(duration)
                        )
                        db.session.add(new_technology)
                        app.logger.info(f'Added new technology {name} in {tech_type}')

            # 削除処理
            for tech in existing_techs:
                if tech.name not in tech_names:
                    db.session.delete(tech)
                    app.logger.info(f'Deleted technology {tech.name} from {tech_type}')

        # 工程の処理
        processes = request.form.getlist('process')
        existing_processes = Process.query.filter_by(project_id=project.id).all()
        existing_process_names = {process.name for process in existing_processes}

        for process_name in ['要件定義', '基本設計', '詳細設計', '実装', '単体テスト', '結合テスト', '受入テスト', '運用・保守']:
            if process_name in processes:
                if process_name not in existing_process_names:
                    new_process = Process(project_id=project.id, name=process_name)
                    db.session.add(new_process)
                    app.logger.info(f'Added new process {process_name}')
            else:
                if process_name in existing_process_names:
                    process = next(p for p in existing_processes if p.name == process_name)
                    db.session.delete(process)
                    app.logger.info(f'Deleted process {process_name}')

        db.session.commit()
        flash('プロジェクトが更新されました。', 'success')
        app.logger.info(f'Project {project_id} updated successfully')
        return redirect(url_for('admin_project_detail', project_id=project_id))

    technologies = {tech_type: Technology.query.filter_by(project_id=project.id, type=tech_type).all() for tech_type in ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']}
    processes = [process.name for process in Process.query.filter_by(project_id=project.id).all()]

    return render_template('admin_project_detail.html', project=project, technologies=technologies, processes=processes)



####################################################################################################
# 
# 関数名：admin_project_delete
# 引数：project_id (int) - 削除するプロジェクトのID
# 返却値：admin_projects.html
# 詳細：指定されたプロジェクトIDに基づいてプロジェクトを削除し、全プロジェクトの一覧ページにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/project/delete/<int:project_id>', methods=['POST'])
@login_required
@admin_required
def admin_project_delete(project_id):
    app.logger.info(f'Deleting project {project_id}')
    project = Project.query.get_or_404(project_id)
    db.session.delete(project)
    db.session.commit()
    flash('プロジェクトが削除されました。', 'success')
    app.logger.info(f'Project {project_id} deleted successfully')
    return redirect(url_for('admin_projects'))
####################################################################################################
# 
# 関数名：admin_user_create
# 引数：なし
# 返却値：admin_user_create.html
# 詳細：新しいユーザーを作成するためのページを提供します。フォームからユーザー情報を入力して、データベースに追加します。成功時にはユーザー一覧ページにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_user_create():
    if request.method == 'POST':
        app.logger.info('Creating a new user')
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
        app.logger.info(f'User {username} created successfully')
        return redirect(url_for('admin_users'))
    
    return render_template('admin_user_create.html')


####################################################################################################
# 
# 関数名：admin_users_pagination
# 引数：page (int) - ページ番号
# 返却値：JSON形式のユーザーデータ
# 詳細：検索条件に基づいてユーザーをページネーションで取得し、JSON形式で返却します。検索条件にはユーザーID、ユーザー名、メールアドレスなどが含まれます。
# 
####################################################################################################
@app.route('/admin/users_pagination', methods=['GET'])
@login_required
@admin_required
def admin_users_pagination():
    app.logger.info('admin_users_pagination start')
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

    app.logger.info('admin_users_pagination end')
    return jsonify({
        'users': users_data,
        'total': total,
        'pages': pages,
        'current_page': page
    })

####################################################################################################
# 
# 関数名：create_admin
# 引数：なし
# 返却値：リダイレクト先のURL
# 詳細：管理者ユーザーを新規作成します。管理者ユーザーのユーザー名とパスワードを取得し、パスワードをハッシュ化してからデータベースに保存します。成功すればダッシュボードにリダイレクトし、失敗すればエラーメッセージを表示します。
# 
####################################################################################################
@app.route('/create_admin', methods=['POST'])
def create_admin():
    app.logger.info('create_admin start')
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
        app.logger.info('create_admin success')
        return redirect(url_for('admin_dashboard'))
    flash('Failed to create admin user. Please check the form and try again.')
    app.logger.info('create_admin failed')
    return redirect(url_for('admin_dashboard'))
####################################################################################################
# 
# 関数名：admin_project_create
# 引数：なし（POSTリクエストでフォームデータを使用）
# 返却値：リダイレクト先のURL
# 詳細：新しいプロジェクトを作成します。フォームから取得したプロジェクト情報と技術情報、工程情報をデータベースに保存し、ダッシュボードにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/project/create', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_project_create():
    app.logger.info('admin_project_create start')
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
        app.logger.info('admin_project_create success')
        return redirect(url_for('admin_dashboard'))

    app.logger.info('admin_project_create render form')
    return render_template('admin_project_create.html')
####################################################################################################
# 
# 関数名：admin_projects_pagination
# 引数：page (int) - ページ番号
# 返却値：JSON形式のプロジェクトデータ
# 詳細：検索条件に基づいてプロジェクトをページネーションで取得し、JSON形式で返却します。検索条件にはプロジェクトID、プロジェクト名、業界、開始月、終了月などが含まれます。
# 
####################################################################################################
@app.route('/admin/projects_pagination', methods=['GET'])
@login_required
@admin_required
def admin_projects_pagination():
    app.logger.info('admin_projects_pagination start')
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

    app.logger.info('admin_projects_pagination end')
    return jsonify({
        'projects': projects_data,
        'total': total,
        'pages': pages,
        'current_page': page
    })




####################################################################################################
# 
# 関数名：admin_logs
# 引数：なし
# 返却値：HTMLテンプレート
# 詳細：ログファイルから最新の10日間のログを読み込み、表示するためのHTMLテンプレートに渡します。ログファイルが存在しない場合はエラーログを記録します。
# 
####################################################################################################
@app.route('/admin/logs')
@login_required
@admin_required
def admin_logs():
    app.logger.info('Fetching logs for admin dashboard')

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

    app.logger.info('Logs fetched and rendered successfully')
    # 最新の10日分のログを表示
    return render_template('admin_logs.html', logs=recent_logs)

####################################################################################################
# 
# 関数名：admin_contacts
# 引数：なし
# 返却値：HTMLテンプレート
# 詳細：データベースから全ての問い合わせを取得し、作成日時順にソートして表示するためのHTMLテンプレートに渡します。
# 
####################################################################################################
@app.route('/admin/contacts')
@login_required
@admin_required
def admin_contacts():
    app.logger.info('Fetching contacts for admin dashboard')

    contacts = Contact.query.order_by(Contact.created_at.desc()).all()
    app.logger.info(f'{len(contacts)} contacts fetched successfully')

    return render_template('admin_contacts.html', contacts=contacts)
####################################################################################################
# 
# 関数名：reply_contact
# 引数：contact_id (int) - 対応するお問い合わせのID
# 返却値：HTMLテンプレートまたはリダイレクト
# 詳細：指定されたお問い合わせIDに基づいて、お問い合わせの詳細を表示し、返信メッセージを送信する機能を提供します。POSTリクエスト時にメールで返信を送信し、成功メッセージを表示して一覧ページにリダイレクトします。
# 
####################################################################################################
@app.route('/admin/contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def reply_contact(contact_id):
    app.logger.info(f'Fetching contact details for contact_id: {contact_id}')

    contact = Contact.query.get_or_404(contact_id)
    if request.method == 'POST':
        reply_message = request.form['reply_message']
        # 件名を手動で設定
        msg = Message('Re: お問い合わせについて',
                    sender='your_email@example.com',
                    recipients=[contact.email])
        msg.body = reply_message
        mail.send(msg)
        app.logger.info(f'Reply sent to contact_id: {contact_id}')
        flash('返信が送信されました。', 'success')
        return redirect(url_for('admin_contacts'))

    return render_template('reply_contact.html', contact=contact)