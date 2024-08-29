
from imports import *
from run import *


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

                if tech_name and tech_duration.isdigit() and int(tech_duration) > 0:
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
    individual_developments = IndividualDevelopment.query.filter_by(user_id=user_id).all()

    project_data = []
    individual_dev_data = []
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

    # 個人開発データの取得
    for dev in individual_developments:
        processes = IndividualProcess.query.filter_by(individual_development_id=dev.id).all()
        technologies = IndividualTechnology.query.filter_by(individual_development_id=dev.id).all()
        
        for tech in technologies:
            tech_type = tech_type_mapping[tech.type]
            if tech_type not in skills_by_category:
                skills_by_category[tech_type] = {}
            
            if tech.name not in skills_by_category[tech_type]:
                skills_by_category[tech_type][tech.name] = tech.duration_months
            else:
                skills_by_category[tech_type][tech.name] += tech.duration_months
        
        individual_dev_data.append({
            'individual_development': dev,
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

    return render_template('sheet.html', user=current_user, projects=project_data, individual_developments=individual_dev_data, skills_by_category=skills_by_category_formatted, tech_type_mapping=tech_type_mapping, link_url=link_url, experience_years=experience_years)


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

            # 重複チェック
            if len(tech_names) != len(set(tech_names)):
                flash('技術名が重複しています。修正してください。', 'error')
                return redirect(url_for('edit_project', project_id=project.id))

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
        current_url = request.url
        return render_template('invalid.html', current_url=current_url)

    # リンクが有効な場合、スキルシートを表示するためデータを受け渡し
    user_id = link.user_id
    user = User.query.get_or_404(user_id)
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
        technologies = Technology.query.filter_by(project_id=project.id).all()
        processes = Process.query.filter_by(project_id=project.id).all()
        
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
            'technologies': technologies,
            'processes': processes
        })

    skills_by_category_formatted = {}
    for category, skills in skills_by_category.items():
        skills_list = [{'name': name, 'duration_months': duration} for name, duration in skills.items()]
        skills_by_category_formatted[category] = skills_list

    return render_template('view_sheet.html', user=user, projects=project_data, skills_by_category=skills_by_category_formatted, link_code=link_code)


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



@app.route('/api/tech_projects/<tech_name>')
@app.route('/api/tech_projects/<tech_name>')
@login_required
def tech_projects(tech_name):
    user_id = current_user.id

    # 技術名に関連するプロジェクトを取得
    projects = Project.query.join(Technology).filter(
        Technology.name == tech_name, 
        Technology.project_id == Project.id, 
        Project.user_id == user_id
    ).all()

    # プロジェクトのIDを元にプロジェクト一覧の順序を一致させる
    project_ids = [p.id for p in Project.query.filter_by(user_id=user_id).all()]
    project_list = [{'number': project_ids.index(project.id) + 1, 'name': project.project_name} for project in projects]

    # 個人開発のIDを元に個人開発一覧の順序を一致させる
    developments = IndividualDevelopment.query.join(IndividualTechnology).filter(
        IndividualTechnology.name == tech_name, 
        IndividualTechnology.individual_development_id == IndividualDevelopment.id, 
        IndividualDevelopment.user_id == user_id
    ).all()

    development_ids = [d.id for d in IndividualDevelopment.query.filter_by(user_id=user_id).all()]
    development_list = [{'number': development_ids.index(development.id) + 1, 'name': development.development_name} for development in developments]

    return jsonify({'projects': project_list, 'developments': development_list})
