
from imports import *
from run import *

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
