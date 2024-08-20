from imports import *
from run import *

####################################################################################################
# 
# 関数名：download_pdf
# 引数：link_code (str) - PDFファイルをダウンロードするためのリンクコード
# 返却値：PDFファイル
# 詳細：指定されたリンクコードに基づいて、関連するユーザーとプロジェクトのデータを取得し、スキルシートのPDFファイルを生成して返却します。リンクが無効な場合はエラーメッセージを表示し、無効なリンク画面にリダイレクトします。
# 
####################################################################################################
@app.route('/download_pdf/<link_code>', methods=['GET'])
def download_pdf(link_code):
    app.logger.info(f'Received request to download PDF with link_code: {link_code}')

    # リンクコードに対応するリンクを取得
    link = Link.query.filter_by(link_code=link_code, is_active=True).first()
    if link is None:
        app.logger.warning(f'Invalid link_code provided: {link_code}')
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

    app.logger.info(f'Generating PDF for user_id: {user_id}')
    # PDF生成
    pdf_buffer = generate_pdf(user, project_data)
    app.logger.info(f'PDF generated successfully for user_id: {user_id}')
    
    return send_file(pdf_buffer, as_attachment=True, download_name='スキルシート_'+user.username+'.pdf', mimetype='application/pdf')
