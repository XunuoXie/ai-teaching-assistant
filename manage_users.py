#!/usr/bin/env python3
"""用户管理工具 - 查看、重置密码、添加用户"""
from app import app, db, User
from werkzeug.security import generate_password_hash
import sys

def print_users():
    """打印所有用户"""
    users = User.query.all()
    print('\n=== 用户列表 ===')
    if not users:
        print('(无用户)')
    else:
        for u in users:
            print(f'  ID: {u.id}')
            print(f'  用户名: {u.username}')
            print(f'  显示名: {u.display_name}')
            print(f'  角色: {u.role}')
            print('  ---')

def reset_password(username, new_password):
    """重置用户密码"""
    user = User.query.filter_by(username=username).first()
    if user:
        user.password = generate_password_hash(new_password)
        db.session.commit()
        print(f'✅ 用户 {username} 密码已重置为: {new_password}')
    else:
        print(f'❌ 用户 {username} 不存在')

def add_user(username, display_name, password, role='student'):
    """添加新用户"""
    if User.query.filter_by(username=username).first():
        print(f'❌ 用户 {username} 已存在')
        return
    user = User(
        username=username,
        display_name=display_name,
        password=generate_password_hash(password),
        role=role
    )
    db.session.add(user)
    db.session.commit()
    print(f'✅ 用户 {username} 创建成功')
    print(f'  密码: {password}')
    print(f'  角色: {role}')

if __name__ == '__main__':
    with app.app_context():
        if len(sys.argv) == 1:
            # 无参数，只显示用户列表
            print_users()
        elif sys.argv[1] == 'reset' and len(sys.argv) == 4:
            # 重置密码: manage_users.py reset username new_password
            reset_password(sys.argv[2], sys.argv[3])
        elif sys.argv[1] == 'add' and len(sys.argv) >= 5:
            # 添加用户: manage_users.py add username display_name password [role]
            role = sys.argv[5] if len(sys.argv) > 5 else 'student'
            add_user(sys.argv[2], sys.argv[3], sys.argv[4], role)
        else:
            print('用法:')
            print('  查看用户: python manage_users.py')
            print('  重置密码: python manage_users.py reset <username> <new_password>')
            print('  添加用户: python manage_users.py add <username> <display_name> <password> [role]')
            print('    role可选: student, teacher, admin (默认student)')
