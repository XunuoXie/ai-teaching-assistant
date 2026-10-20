from app import app, db, User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    
    # 检查是否已存在用户
    if not User.query.first():
        # 创建默认教师账号
        teacher = User(
            username='teacher',
            display_name='张老师',
            password=generate_password_hash('teacher123'),
            role='teacher'
        )
        
        # 创建默认学生账号
        student = User(
            username='student',
            display_name='李同学',
            password=generate_password_hash('student123'),
            role='student'
        )
        
        # 创建默认管理员账号
        admin = User(
            username='admin',
            display_name='管理员',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        
        db.session.add(teacher)
        db.session.add(student)
        db.session.add(admin)
        db.session.commit()
        
        print('数据库初始化成功！')
        print('默认账号已创建：')
        print('  教师账号：teacher / teacher123')
        print('  学生账号：student / student123')
        print('  管理员账号：admin / admin123')
    else:
        print('数据库已存在用户，跳过初始化')
        print('现有用户列表：')
        users = User.query.all()
        for u in users:
            print(f'  - {u.username} ({u.role}) - {u.display_name}')
