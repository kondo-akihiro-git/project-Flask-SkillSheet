from imports import *
from run import *

@app.route('/individual_input', methods=['GET', 'POST'])
@login_required
def individual_input():
    if request.method == 'POST':
        # フォームからデータを取得
        start_month = request.form.get('start_month')
        end_month = request.form.get('end_month')
        development_name = request.form.get('development_name')
        development_summary = request.form.get('development_summary')

        # 新しい個人開発レコードの作成
        new_dev = IndividualDevelopment(
            user_id=current_user.id,
            start_month=start_month,
            end_month=end_month,
            development_name=development_name,
            development_summary=development_summary
        )
        db.session.add(new_dev)
        db.session.commit()

        # 技術とプロセスの保存
        tech_types = ['os', 'language', 'framework', 'database', 'containertech', 'cicd', 'logging', 'tools']
        for tech_type in tech_types:
            index = 0
            while f'{tech_type}_{index}' in request.form:
                tech_name = request.form.get(f'{tech_type}_{index}')
                tech_duration = request.form.get(f'{tech_type}_{index}_num', '0')

                if tech_name and tech_duration.isdigit() and int(tech_duration) > 0:
                    tech = IndividualTechnology(
                        individual_development_id=new_dev.id,
                        type=tech_type,
                        name=tech_name,
                        duration_months=int(tech_duration)
                    )
                    db.session.add(tech)
                index += 1

        # 担当した工程の保存
        processes = request.form.getlist('process')
        for process_name in processes:
            if process_name:
                process = IndividualProcess(
                    individual_development_id=new_dev.id,
                    name=process_name
                )
                db.session.add(process)

        db.session.commit()
        flash('個人開発情報が正常に保存されました。', 'success')
        return redirect(url_for('individual_input'))

    return render_template('individual_input.html')
