from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from ..models import User
from ..extensions import db
from ..config import Config
from ..utils.auto_assign import auto_assign_student

bp = Blueprint('api_auth', __name__)


def create_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    
    if user and check_password_hash(user.password, password):
        token = create_token(user)
        return jsonify({
            'success': True,
            'token': token,
            'user': {
                'id': user.id,
                'username': user.username,
                'display_name': user.display_name,
                'role': user.role
            }
        })
    
    return jsonify({'success': False, 'message': '用户名或密码错误'}), 401


@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    display_name = data.get('display_name')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    
    hashed = generate_password_hash(password)
    user = User(username=username, display_name=display_name, password=hashed, role=role)
    db.session.add(user)
    db.session.commit()

    if role == 'student':
        auto_assign_student(user.id)

    return jsonify({'success': True, 'message': '注册成功'})


@bp.route('/me', methods=['GET'])
def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({'success': False, 'message': '未登录'}), 401
    
    try:
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        return jsonify({
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'role': user.role
        })
    except Exception:
        return jsonify({'success': False, 'message': '无效的token'}), 401


@bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({'success': True, 'message': '登出成功'})
