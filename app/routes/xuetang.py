from flask import Blueprint, request, jsonify, session, current_app
from datetime import datetime, timedelta
import jwt
from werkzeug.security import generate_password_hash
from ..models import User, XuexitongStudent
from ..extensions import db
from ..config import Config
from ..utils.auto_assign import auto_assign_student

bp = Blueprint('xuetang', __name__, url_prefix='/api/xuetang')


def _get_teacher_cpis():
    raw = Config.XUETANG_TEACHER_CPIS
    if not raw:
        return set()
    return {c.strip() for c in raw.split(',') if c.strip()}


def is_teacher_cpi(cpi):
    return cpi in _get_teacher_cpis()


def create_token(user):
    payload = {
        'user_id': user.id,
        'username': user.username,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(days=7)
    }
    return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')


@bp.route('/check', methods=['GET'])
def check():
    # Try session first (same-origin), fallback to query params (cross-origin)
    xuetang_params = session.get('xuetang_params')
    if not xuetang_params or not xuetang_params.get('cpi'):
        cpi = request.args.get('cpi')
        if cpi:
            xuetang_params = {
                'cpi': cpi,
                'courseId': request.args.get('courseId', ''),
                'clazzId': request.args.get('clazzId', '')
            }

    if not xuetang_params or not xuetang_params.get('cpi'):
        return jsonify({'hasParams': False, 'registered': False})

    cpi = xuetang_params['cpi']
    binding = XuexitongStudent.query.filter_by(cpi=cpi).first()

    if not binding:
        if is_teacher_cpi(cpi):
            # 教师 CPI 自动创建账号，跳过登记
            username = f'xt_{cpi[:20]}'
            if User.query.filter_by(username=username).first():
                import uuid
                username = f'xt_{uuid.uuid4().hex[:12]}'

            user = User(
                username=username,
                display_name=f'教师_{cpi[:8]}',
                password=generate_password_hash(cpi),
                role='teacher'
            )
            db.session.add(user)
            db.session.flush()

            binding = XuexitongStudent(
                cpi=cpi,
                course_id=xuetang_params.get('courseId', ''),
                clazz_id=xuetang_params.get('clazzId', ''),
                name=user.display_name,
                student_id='',
                user_id=user.id
            )
            db.session.add(binding)
            db.session.commit()

            token = create_token(user)
            return jsonify({
                'registered': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'display_name': user.display_name,
                    'role': user.role
                }
            })

        return jsonify({
            'hasParams': True,
            'registered': False,
            'isTeacherCpi': False,
            'courseId': xuetang_params.get('courseId'),
            'clazzId': xuetang_params.get('clazzId')
        })

    user = User.query.get(binding.user_id)
    if not user:
        return jsonify({'hasParams': True, 'registered': False}), 500

    token = create_token(user)
    return jsonify({
        'registered': True,
        'token': token,
        'user': {
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'role': user.role
        }
    })


@bp.route('/register', methods=['POST'])
def register():
    xuetang_params = session.get('xuetang_params')
    if not xuetang_params or not xuetang_params.get('cpi'):
        # Fallback: allow params from query string or request body
        data = request.get_json(silent=True) or {}
        cpi = request.args.get('cpi') or data.get('cpi')
        if cpi:
            xuetang_params = {
                'cpi': cpi,
                'courseId': request.args.get('courseId', '') or data.get('courseId', ''),
                'clazzId': request.args.get('clazzId', '') or data.get('clazzId', '')
            }

    if not xuetang_params or not xuetang_params.get('cpi'):
        return jsonify({'success': False, 'message': '缺少学习通参数，请从学习通跳转访问'}), 400

    data = request.get_json()
    name = data.get('name', '').strip()
    student_id = data.get('student_id', '').strip()

    if not name or not student_id:
        return jsonify({'success': False, 'message': '姓名和学号不能为空'}), 400

    cpi = xuetang_params['cpi']
    course_id = xuetang_params.get('courseId', '')
    clazz_id = xuetang_params.get('clazzId', '')

    if XuexitongStudent.query.filter_by(cpi=cpi).first():
        return jsonify({'success': False, 'message': '该账户已登记'}), 400

    username = f'xt_{cpi[:20]}'
    if User.query.filter_by(username=username).first():
        import uuid
        username = f'xt_{uuid.uuid4().hex[:12]}'

    role = 'teacher' if is_teacher_cpi(cpi) else 'student'

    user = User(
        username=username,
        display_name=name,
        password=generate_password_hash(student_id),
        role=role
    )
    db.session.add(user)
    db.session.flush()

    binding = XuexitongStudent(
        cpi=cpi,
        course_id=course_id,
        clazz_id=clazz_id,
        name=name,
        student_id=student_id,
        user_id=user.id
    )
    db.session.add(binding)
    db.session.commit()

    if role == 'student':
        auto_assign_student(user.id)

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
