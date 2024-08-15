# create_admin.py

from run import app, db, User
from werkzeug.security import generate_password_hash

def create_admin(username, mail, password):
    with app.app_context():
        # ハッシュ化されたパスワードを作成
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        # 管理者ユーザーを作成
        admin_user = User(username=username, email=mail, password=hashed_password,is_active=True, is_admin=True)
        
        # データベースに追加
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user {username} created successfully!")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        print("Usage: python create_admin.py <username> <email> <password>")
        sys.exit(1)
    
    username = sys.argv[1]
    mail = sys.argv[2]
    password = sys.argv[3]
    create_admin(username, mail, password)
