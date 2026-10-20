
import functools
from flask import session, redirect, url_for, render_template
from ..models import User


def require_role(role):
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            if 'user_id' not in session:
                return redirect(url_for('auth.login'))
            user = User.query.get(session['user_id'])
            if not user:
                session.clear()
                return redirect(url_for('auth.login'))
            if user.role != role and user.role != 'admin':
                if user.role == 'student':
                    return render_template(
                        'error.html',
                        message='无权访问',
                        details='学生账号无法访问教师端功能，请使用教师或管理员账号登录。',
                        back_url=url_for('student.dashboard')
                    ), 403
                else:
                    return render_template(
                        'error.html',
                        message='无权访问',
                        details='您的账号没有权限访问此功能。',
                        back_url=url_for('main.home')
                    ), 403
            return f(*args, **kwargs)
        return wrapper
    return decorator
