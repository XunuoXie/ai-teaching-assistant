
from flask import Blueprint, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from ..models import User
from ..extensions import db

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        display_name = request.form['display_name']
        password = request.form['password']
        role = request.form.get('role', 'student')
        
        if User.query.filter_by(username=username).first():
            return "用户名已存在", 400
        
        hashed = generate_password_hash(password)
        user = User(username=username, display_name=display_name, password=hashed, role=role)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('auth.login'))
    return render_template('register.html')


@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['display_name'] = user.display_name
            session['role'] = user.role
            
            if user.role == 'teacher' or user.role == 'admin':
                return redirect(url_for('teacher.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        return "用户名或密码错误", 401
    return render_template('login.html')


@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('auth.login'))


@bp.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    
    if request.method == 'POST':
        display_name = request.form.get('display_name')
        new_password = request.form.get('new_password')
        
        if display_name:
            user.display_name = display_name
        if new_password:
            user.password = generate_password_hash(new_password)
        
        db.session.commit()
        session['display_name'] = user.display_name
        return "修改成功", 200
    
    return render_template('profile.html', user=user)
