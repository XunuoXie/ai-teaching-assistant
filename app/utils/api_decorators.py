from functools import wraps
from flask import request, jsonify, g
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
import logging
from ..config import Config
from ..models import User

logger = logging.getLogger(__name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            logger.info('No Authorization header provided')
            return jsonify({'success': False, 'message': '未登录'}), 401
        
        try:
            parts = auth_header.split(' ')
            if len(parts) != 2 or parts[0].lower() != 'bearer':
                logger.info('Invalid Authorization header format')
                return jsonify({'success': False, 'message': '无效的授权格式'}), 401
            
            token = parts[1]
            logger.info(f'Token received: {token[:20]}...')
            
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            
            if not user:
                logger.info('User not found')
                return jsonify({'success': False, 'message': '用户不存在'}), 404
            
            g.current_user = user
            return f(*args, **kwargs)
        except ExpiredSignatureError:
            logger.info('Token expired')
            return jsonify({'success': False, 'message': 'token已过期'}), 401
        except InvalidTokenError as e:
            logger.info(f'Invalid token: {str(e)}')
            return jsonify({'success': False, 'message': '无效的token'}), 401
        except Exception as e:
            logger.error(f'Unexpected error during auth: {str(e)}')
            return jsonify({'success': False, 'message': f'认证错误: {str(e)}'}), 401
    
    return decorated_function


def teacher_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.current_user.role not in ['teacher', 'admin']:
            return jsonify({'success': False, 'message': '需要教师权限'}), 403
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if g.current_user.role != 'admin':
            return jsonify({'success': False, 'message': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated_function
