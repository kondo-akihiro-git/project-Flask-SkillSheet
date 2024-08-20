from imports import *
from run import *


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