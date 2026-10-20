from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..models import User, Assignment, Submission, StudentClass, Class, ChatSession, ChatMessage
from ..extensions import db
from ..utils.api_decorators import login_required, teacher_required, admin_required
from ..utils.auto_assign import auto_assign_student
from ..utils.code_executor import execute_python_code
from ..utils.security import is_safe_code
from ..utils.auto_grader import auto_grade_submission
import json
import logging
from flask import url_for

logger = logging.getLogger(__name__)

bp = Blueprint('api', __name__)


@bp.route('/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    if g.current_user.role in ['teacher', 'admin']:
        total_assignments = Assignment.query.filter_by(created_by=g.current_user.id).count()
        total_students = User.query.filter_by(role='student').count()
        scored_submissions = Submission.query.filter(Submission.score != None).count()
        total_submissions = scored_submissions
    else:
        class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=g.current_user.id).all()]
        assignments = Assignment.query.filter(
            (Assignment.class_id == None) | (Assignment.class_id.in_(class_ids))
        ).all()
        total_assignments = len(assignments)
        submissions = Submission.query.filter_by(student_id=g.current_user.id).all()
        scored_submissions = len([s for s in submissions if s.score is not None])
        total_submissions = len(submissions)
        unscored_submissions = total_submissions - scored_submissions
    
    return jsonify({
        'totalAssignments': total_assignments,
        'totalStudents': total_students if g.current_user.role in ['teacher', 'admin'] else 0,
        'scoredSubmissions': scored_submissions,
        'totalSubmissions': total_submissions
    })


@bp.route('/classes', methods=['GET'])
@teacher_required
def get_classes():
    classes = Class.query.all()
    result = []
    for cls in classes:
        student_count = StudentClass.query.filter_by(class_id=cls.id).count()
        result.append({
            'id': cls.id,
            'name': cls.name,
            'description': cls.description,
            'created_at': cls.created_at.isoformat() if cls.created_at else None,
            'student_count': student_count
        })
    return jsonify(result)


@bp.route('/classes', methods=['POST'])
@teacher_required
def create_class():
    data = request.get_json()
    cls = Class(
        name=data['name'],
        description=data.get('description', ''),
        created_by=g.current_user.id
    )
    db.session.add(cls)
    db.session.commit()
    return jsonify({'success': True, 'id': cls.id})


@bp.route('/classes/<int:class_id>', methods=['PUT'])
@teacher_required
def update_class(class_id):
    cls = Class.query.get_or_404(class_id)
    data = request.get_json()
    cls.name = data.get('name', cls.name)
    cls.description = data.get('description', cls.description)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/classes/<int:class_id>', methods=['DELETE'])
@teacher_required
def delete_class(class_id):
    cls = Class.query.get_or_404(class_id)
    StudentClass.query.filter_by(class_id=class_id).delete()
    Assignment.query.filter_by(class_id=class_id).update({'class_id': None})
    db.session.delete(cls)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/classes/<int:class_id>/students', methods=['GET'])
@teacher_required
def get_class_students(class_id):
    class_students = db.session.query(User).join(StudentClass).filter(StudentClass.class_id == class_id).all()
    all_students = User.query.filter_by(role='student').all()
    student_ids_in_class = {s.id for s in class_students}
    available_students = [s for s in all_students if s.id not in student_ids_in_class]
    
    return jsonify({
        'class_students': [{'id': s.id, 'username': s.username, 'display_name': s.display_name} for s in class_students],
        'available_students': [{'id': s.id, 'username': s.username, 'display_name': s.display_name} for s in available_students]
    })


@bp.route('/classes/<int:class_id>/students', methods=['POST'])
@teacher_required
def add_student_to_class(class_id):
    data = request.get_json()
    student_id = data.get('student_id')
    if StudentClass.query.filter_by(class_id=class_id, student_id=student_id).first():
        return jsonify({'success': False, 'message': '学生已在班级中'}), 400
    
    sc = StudentClass(class_id=class_id, student_id=student_id)
    db.session.add(sc)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/classes/<int:class_id>/students/<int:student_id>', methods=['DELETE'])
@teacher_required
def remove_student_from_class(class_id, student_id):
    sc = StudentClass.query.filter_by(class_id=class_id, student_id=student_id).first()
    if sc:
        db.session.delete(sc)
        db.session.commit()
    return jsonify({'success': True})


@bp.route('/assignments', methods=['GET'])
@login_required
def get_assignments():
    if g.current_user.role == 'admin':
        assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    elif g.current_user.role == 'teacher':
        assignments = Assignment.query.filter_by(created_by=g.current_user.id).order_by(Assignment.created_at.desc()).all()
    else:
        class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=g.current_user.id).all()]
        assignments = Assignment.query.filter(
            (Assignment.class_id == None) | (Assignment.class_id.in_(class_ids))
        ).order_by(Assignment.created_at.desc()).all()
    
    classes = Class.query.all()
    class_map = {c.id: c.name for c in classes}
    
    student_submissions = {}
    if g.current_user.role == 'student':
        submissions = Submission.query.filter_by(student_id=g.current_user.id).all()
        student_submissions = {s.assignment_id: s for s in submissions}
    
    result = []
    for assignment in assignments:
        assignment_data = {
            'id': assignment.id,
            'title': assignment.title,
            'description': assignment.description,
            'deadline': assignment.deadline.isoformat() if assignment.deadline else None,
            'class_id': assignment.class_id,
            'class_name': class_map.get(assignment.class_id) if assignment.class_id else None,
            'total_score': assignment.total_score,
            'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
            'is_deadline_urgent': assignment.is_deadline_urgent()
        }
        
        if g.current_user.role == 'student' and assignment.id in student_submissions:
            sub = student_submissions[assignment.id]
            assignment_data['submitted_at'] = sub.submitted_at.isoformat() if sub.submitted_at else None
            assignment_data['score'] = sub.score
            assignment_data['feedback'] = sub.feedback
        
        result.append(assignment_data)
    return jsonify(result)


@bp.route('/assignments', methods=['POST'])
@teacher_required
def create_assignment():
    data = request.get_json()
    deadline = None
    if data.get('deadline'):
        deadline = datetime.fromisoformat(data['deadline'])
    
    assignment = Assignment(
        title=data['title'],
        description=data.get('description', ''),
        deadline=deadline,
        class_id=data.get('class_id'),
        total_score=data.get('total_score', 100),
        created_by=g.current_user.id
    )
    db.session.add(assignment)
    db.session.commit()
    return jsonify({'success': True, 'id': assignment.id})


@bp.route('/assignments/<int:assignment_id>', methods=['GET'])
@login_required
def get_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    classes = Class.query.all()
    class_map = {c.id: c.name for c in classes}
    
    submission = None
    if g.current_user.role == 'student':
        submission = Submission.query.filter_by(
            assignment_id=assignment_id,
            student_id=g.current_user.id
        ).first()
    
    submission_data = None
    if submission:
        images = []
        if submission.images:
            try:
                image_list = json.loads(submission.images)
                images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
            except:
                pass
        
        submission_data = {
            'id': submission.id,
            'code': submission.code,
            'stdout': submission.stdout,
            'stderr': submission.stderr,
            'images': images,
            'score': submission.score,
            'feedback': submission.feedback,
            'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
        }
    
    return jsonify({
        'id': assignment.id,
        'title': assignment.title,
        'description': assignment.description,
        'deadline': assignment.deadline.isoformat() if assignment.deadline else None,
        'class_id': assignment.class_id,
        'class_name': class_map.get(assignment.class_id) if assignment.class_id else None,
        'total_score': assignment.total_score,
        'created_at': assignment.created_at.isoformat() if assignment.created_at else None,
        'submission': submission_data
    })


@bp.route('/assignments/<int:assignment_id>', methods=['PUT'])
@teacher_required
def update_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    data = request.get_json()
    assignment.title = data.get('title', assignment.title)
    assignment.description = data.get('description', assignment.description)
    if 'deadline' in data:
        assignment.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
    assignment.class_id = data.get('class_id', assignment.class_id)
    assignment.total_score = data.get('total_score', assignment.total_score)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/assignments/<int:assignment_id>', methods=['DELETE'])
@teacher_required
def delete_assignment(assignment_id):
    assignment = Assignment.query.get_or_404(assignment_id)
    Submission.query.filter_by(assignment_id=assignment_id).delete()
    db.session.delete(assignment)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/assignments/<int:assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    print(f"[DEBUG] 收到作业提交请求: assignment_id={assignment_id}")
    print(f"[DEBUG] 当前用户: {g.current_user.username} (角色: {g.current_user.role})")
    
    if g.current_user.role != 'student':
        print(f"[DEBUG] 权限检查失败: 用户不是学生")
        return jsonify({'success': False, 'message': '只有学生可以提交作业'}), 403
    
    assignment = Assignment.query.get_or_404(assignment_id)
    print(f"[DEBUG] 作业信息: {assignment.title}")
    
    if assignment.deadline and datetime.now() > assignment.deadline:
        print(f"[DEBUG] 截止时间检查失败: 已过期")
        return jsonify({'success': False, 'message': '作业已过截止时间，无法提交'}), 400
    
    data = request.get_json()
    print(f"[DEBUG] 请求数据: {data.keys() if data else '空'}")
    
    code = data.get('code', '')
    print(f"[DEBUG] 代码长度: {len(code)}")
    
    if not is_safe_code(code):
        print(f"[DEBUG] 安全检查失败")
        return jsonify({'success': False, 'message': '检测到不安全代码'}), 400
    
    print(f"[DEBUG] 开始执行代码...")
    stdout, stderr, images = execute_python_code(code)
    print(f"[DEBUG] 代码执行完成: stdout={len(stdout)}, stderr={len(stderr)}, images={len(images) if images else 0}")
    
    image_str = json.dumps(images) if images else None
    
    submission = Submission.query.filter_by(
        assignment_id=assignment_id,
        student_id=g.current_user.id
    ).order_by(Submission.submitted_at.desc()).first()
    
    if submission:
        submission.code = code
        submission.stdout = stdout
        submission.stderr = stderr
        submission.images = image_str
        submission.submitted_at = datetime.now()
    else:
        submission = Submission(
            assignment_id=assignment_id,
            student_id=g.current_user.id,
            code=code,
            stdout=stdout,
            stderr=stderr,
            images=image_str
        )
        db.session.add(submission)
    
    db.session.commit()
    
    # ========== 自动评分功能 ==========
    score, feedback = auto_grade_submission(
        assignment_id=assignment_id,
        code=code,
        stdout=stdout,
        stderr=stderr,
        images=images
    )
    logger.info(f"自动评分完成: assignment_id={assignment_id}, score={score}")
    
    # 更新提交记录的分数和反馈
    submission.score = score
    submission.feedback = feedback
    db.session.commit()
    # ========== 自动评分功能结束 ==========
    
    image_urls = []
    if images:
        for img in images:
            image_urls.append(url_for('static', filename=f'outputs/{img}'))
    
    return jsonify({
        'success': True,
        'stdout': stdout,
        'stderr': stderr,
        'images': image_urls,
        'score': score,
        'feedback': feedback
    })


@bp.route('/admin/users', methods=['GET'])
@admin_required
def get_all_users():
    users = User.query.all()
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'username': user.username,
            'display_name': user.display_name,
            'role': user.role,
            'created_at': user.created_at.isoformat() if hasattr(user, 'created_at') and user.created_at else None
        })
    return jsonify(result)


@bp.route('/admin/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    username = data.get('username')
    display_name = data.get('display_name')
    password = data.get('password')
    role = data.get('role', 'student')
    
    if not username or not display_name or not password:
        return jsonify({'success': False, 'message': '用户名、姓名和密码不能为空'}), 400
    
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '用户名已存在'}), 400
    
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash(password)
    user = User(username=username, display_name=display_name, password=hashed, role=role)
    db.session.add(user)
    db.session.commit()

    if role == 'student':
        auto_assign_student(user.id)

    return jsonify({'success': True, 'id': user.id})


@bp.route('/admin/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    
    if 'display_name' in data:
        user.display_name = data['display_name']
    if 'role' in data:
        user.role = data['role']
    
    if 'password' in data and data['password']:
        from werkzeug.security import generate_password_hash
        user.password = generate_password_hash(data['password'])
    
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/admin/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if user.role == 'admin':
        return jsonify({'success': False, 'message': '不能删除管理员账户'}), 400
    
    StudentClass.query.filter_by(student_id=user_id).delete()
    Submission.query.filter_by(student_id=user_id).delete()
    Assignment.query.filter_by(created_by=user_id).delete()
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/admin/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    user = User.query.get_or_404(user_id)
    data = request.get_json()
    new_password = data.get('password')
    
    if not new_password:
        return jsonify({'success': False, 'message': '新密码不能为空'}), 400
    
    from werkzeug.security import generate_password_hash
    user.password = generate_password_hash(new_password)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/submissions', methods=['GET'])
@teacher_required
def get_submissions():
    assignment_id = request.args.get('assignment_id', type=int)
    class_id = request.args.get('class_id', type=int)
    
    if g.current_user.role == 'teacher':
        teacher_assignment_ids = [a.id for a in Assignment.query.filter_by(created_by=g.current_user.id).all()]
        query = Submission.query.filter(Submission.assignment_id.in_(teacher_assignment_ids))
    else:
        query = Submission.query
    
    if assignment_id and assignment_id > 0:
        query = query.filter_by(assignment_id=assignment_id)
    
    if class_id and class_id > 0:
        assignment_ids = [a.id for a in Assignment.query.filter_by(class_id=class_id).all()]
        if assignment_ids:
            query = query.filter(Submission.assignment_id.in_(assignment_ids))
        else:
            query = query.filter_by(id=0)
    
    submissions = query.all()
    assignments = Assignment.query.all()
    students = User.query.filter_by(role='student').all()
    
    student_map = {s.id: s.display_name for s in students}
    assignment_map = {a.id: a.title for a in assignments}
    
    result = []
    for submission in submissions:
        result.append({
            'id': submission.id,
            'assignment_id': submission.assignment_id,
            'assignment_title': assignment_map.get(submission.assignment_id),
            'student_id': submission.student_id,
            'student_name': student_map.get(submission.student_id),
            'score': submission.score,
            'feedback': submission.feedback,
            'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
        })
    return jsonify(result)


@bp.route('/submissions/<int:submission_id>', methods=['GET'])
@teacher_required
def get_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    student = User.query.get(submission.student_id)
    assignment = Assignment.query.get(submission.assignment_id)
    
    images = []
    if submission.images:
        try:
            image_list = json.loads(submission.images)
            images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
        except:
            pass
    
    return jsonify({
        'id': submission.id,
        'student': {
            'id': student.id,
            'display_name': student.display_name
        },
        'assignment': {
            'id': assignment.id,
            'title': assignment.title,
            'total_score': assignment.total_score
        },
        'code': submission.code,
        'stdout': submission.stdout,
        'stderr': submission.stderr,
        'images': images,
        'score': submission.score,
        'feedback': submission.feedback,
        'submitted_at': submission.submitted_at.isoformat() if submission.submitted_at else None
    })


@bp.route('/submissions/<int:submission_id>/grade', methods=['POST'])
@teacher_required
def grade_submission(submission_id):
    submission = Submission.query.get_or_404(submission_id)
    data = request.get_json()
    if 'score' in data:
        submission.score = data['score'] if data['score'] is not None else None
    if 'feedback' in data:
        submission.feedback = data['feedback']
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/students', methods=['GET'])
@teacher_required
def get_students():
    students = User.query.filter_by(role='student').all()
    classes = Class.query.all()
    
    student_class_map = {}
    for student in students:
        student_classes = StudentClass.query.filter_by(student_id=student.id).all()
        student_class_map[student.id] = [{'id': c.class_id, 'name': Class.query.get(c.class_id).name} for c in student_classes]
    
    result = []
    for student in students:
        result.append({
            'id': student.id,
            'username': student.username,
            'display_name': student.display_name,
            'classes': student_class_map.get(student.id, [])
        })
    return jsonify(result)


@bp.route('/students', methods=['POST'])
@teacher_required
def create_student():
    data = request.get_json()
    username = data.get('username')
    display_name = data.get('display_name')
    password = data.get('password')
    
    if not username or not display_name or not password:
        return jsonify({'success': False, 'message': '学号、姓名和密码不能为空'}), 400
    
    # 检查学号是否已存在
    if User.query.filter_by(username=username).first():
        return jsonify({'success': False, 'message': '该学号已存在'}), 400
    
    from werkzeug.security import generate_password_hash
    hashed = generate_password_hash(password)
    user = User(username=username, display_name=display_name, password=hashed, role='student')
    db.session.add(user)
    db.session.commit()
    
    return jsonify({'success': True, 'id': user.id})


@bp.route('/students/<int:student_id>', methods=['GET'])
@teacher_required
def get_student_detail(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'success': False, 'message': '只能查看学生详情'}), 400
    
    # 获取学生班级
    student_classes = db.session.query(Class).join(StudentClass).filter(StudentClass.student_id == student_id).all()
    
    # 获取所有作业
    all_assignments = Assignment.query.all()
    
    # 获取学生提交记录
    submissions = Submission.query.filter_by(student_id=student_id).all()
    submission_map = {s.assignment_id: s for s in submissions}
    
    # 整理作业完成情况
    assignments_status = []
    for assignment in all_assignments:
        submission = submission_map.get(assignment.id)
        assignments_status.append({
            'id': assignment.id,
            'title': assignment.title,
            'deadline': assignment.deadline.isoformat() if assignment.deadline else None,
            'total_score': assignment.total_score,
            'submitted': submission is not None,
            'submitted_at': submission.submitted_at.isoformat() if submission and submission.submitted_at else None,
            'score': submission.score if submission else None,
            'feedback': submission.feedback if submission else None
        })
    
    return jsonify({
        'id': student.id,
        'username': student.username,
        'display_name': student.display_name,
        'classes': [{'id': c.id, 'name': c.name} for c in student_classes],
        'assignments': assignments_status
    })


@bp.route('/students/<int:student_id>', methods=['DELETE'])
@teacher_required
def delete_student(student_id):
  student = User.query.get_or_404(student_id)
  if student.role != 'student':
    return jsonify({'success': False, 'message': '只能删除学生用户'}), 400
  
  StudentClass.query.filter_by(student_id=student_id).delete()
  Submission.query.filter_by(student_id=student_id).delete()
  db.session.delete(student)
  db.session.commit()
  return jsonify({'success': True})


@bp.route('/students/<int:student_id>/add-class', methods=['POST'])
@teacher_required
def add_class_to_student(student_id):
  data = request.get_json()
  class_id = data.get('class_id')
  if not class_id:
    return jsonify({'success': False, 'message': '缺少班级ID'}), 400
  
  if StudentClass.query.filter_by(student_id=student_id, class_id=class_id).first():
    return jsonify({'success': False, 'message': '学生已在该班级中'}), 400
  
  sc = StudentClass(student_id=student_id, class_id=class_id)
  db.session.add(sc)
  db.session.commit()
  return jsonify({'success': True})


@bp.route('/students/<int:student_id>/remove-class', methods=['POST'])
@teacher_required
def remove_class_from_student(student_id):
  data = request.get_json()
  class_id = data.get('class_id')
  if not class_id:
    return jsonify({'success': False, 'message': '缺少班级ID'}), 400
  
  StudentClass.query.filter_by(student_id=student_id, class_id=class_id).delete()
  db.session.commit()
  return jsonify({'success': True})


@bp.route('/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    message = data.get('message', '')
    
    try:
        from ..utils.llm import call_llm_and_execute
        response, _, _ = call_llm_and_execute([{"role": "user", "content": message}])
        
        return jsonify({
            'success': True,
            'reply': response
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'reply': f"抱歉，发生了错误：{str(e)}"
        }), 500


@bp.route('/execute-code', methods=['POST'])
@login_required
def execute_code():
    data = request.get_json()
    code = data.get('code', '')
    
    if not is_safe_code(code):
        return jsonify({'success': False, 'message': '检测到不安全代码'}), 400
    
    stdout, stderr, images = execute_python_code(code)
    
    image_urls = []
    if images:
        for img in images:
            image_urls.append(url_for('static', filename=f'outputs/{img}'))
    
    return jsonify({
        'success': True,
        'stdout': stdout,
        'stderr': stderr,
        'images': image_urls
    })


@bp.route('/chat/sessions', methods=['GET'])
@login_required
def get_chat_sessions():
    sessions = ChatSession.query.filter_by(user_id=g.current_user.id).order_by(ChatSession.updated_at.desc()).all()
    
    result = []
    for session in sessions:
        last_message = session.messages[-1].content if session.messages else ''
        result.append({
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'last_message': last_message[:50] + '...' if len(last_message) > 50 else last_message,
            'message_count': len(session.messages)
        })
    
    return jsonify(result)


@bp.route('/chat/sessions', methods=['POST'])
@login_required
def create_chat_session():
    data = request.get_json()
    title = data.get('title', '新对话')
    
    session = ChatSession(user_id=g.current_user.id, title=title)
    db.session.add(session)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'session': {
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        }
    })


@bp.route('/chat/sessions/<int:session_id>', methods=['GET'])
@login_required
def get_chat_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first_or_404()
    
    messages = []
    for msg in session.messages:
        images = []
        if msg.images:
            try:
                image_list = json.loads(msg.images)
                images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
            except:
                pass
        
        messages.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'stdout': msg.stdout,
            'stderr': msg.stderr,
            'images': images,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({
        'id': session.id,
        'title': session.title,
        'created_at': session.created_at.isoformat(),
        'updated_at': session.updated_at.isoformat(),
        'messages': messages
    })


@bp.route('/chat/sessions/<int:session_id>', methods=['PUT'])
@login_required
def update_chat_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first_or_404()
    
    data = request.get_json()
    if 'title' in data:
        session.title = data['title']
        session.updated_at = datetime.now()
        db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/chat/sessions/<int:session_id>', methods=['DELETE'])
@login_required
def delete_chat_session(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first_or_404()
    db.session.delete(session)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/chat/sessions/<int:session_id>/messages', methods=['POST'])
@login_required
def send_chat_message(session_id):
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first_or_404()
    
    data = request.get_json()
    message_content = data.get('message', '')
    
    user_message = ChatMessage(
        session_id=session_id,
        role='user',
        content=message_content
    )
    db.session.add(user_message)
    
    try:
        from ..utils.llm import call_llm_and_execute
        
        # 获取该会话的所有历史消息
        historical_messages = ChatMessage.query.filter_by(session_id=session_id).order_by(ChatMessage.created_at.asc()).all()
        
        # 构建完整的对话上下文
        messages = []
        
        # 添加系统提示词
        system_prompt = """你是一个专业的 Python 代码助手，专门帮助学生学习编程和数据分析。

你的主要能力：
1. 编写和解释 Python 代码
2. 使用 matplotlib 生成图表和动画
3. 使用 numpy、pandas 进行数据处理
4. 执行代码并解释结果

重要规则：
- 如果需要生成图表或可视化代码，使用 matplotlib，确保代码完整可运行
- 如果用户请求动画，系统会自动将 FuncAnimation 保存为 GIF
- 用简洁清晰的语言解释代码
- 在回复中包含代码时，使用 ```python 代码块 ``` 包裹
- 不要在代码中使用 os、subprocess、eval 等危险操作"""
        
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息（限制最近的消息数量以节省 token）
        MAX_HISTORY_MESSAGES = 20  # 最多保留最近 20 轮对话
        recent_messages = historical_messages[-MAX_HISTORY_MESSAGES*2:] if len(historical_messages) > MAX_HISTORY_MESSAGES*2 else historical_messages
        
        for msg in recent_messages:
            # 只添加有实际内容的回复
            if msg.role in ['user', 'assistant'] and msg.content:
                messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": message_content})
        
        logger.info(f"聊天请求: 会话ID={session_id}, 消息数={len(messages)}")
        response_text, _, _ = call_llm_and_execute(messages)
        logger.info(f"聊天响应: 长度={len(response_text) if response_text else 0}")
        
        bot_message = ChatMessage(
            session_id=session_id,
            role='assistant',
            content=response_text
        )
        db.session.add(bot_message)
        
        session.updated_at = datetime.now()
        db.session.commit()
        
        logger.info(f"消息已保存: ID={bot_message.id}")
        
        return jsonify({
            'success': True,
            'message': {
                'id': bot_message.id,
                'role': bot_message.role,
                'content': bot_message.content,
                'created_at': bot_message.created_at.isoformat()
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'reply': f"抱歉，发生了错误：{str(e)}"
        }), 500


@bp.route('/teacher/students/<int:student_id>/chat-sessions', methods=['GET'])
@teacher_required
def get_student_chat_sessions(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'success': False, 'message': '只能查看学生的聊天记录'}), 400
    
    sessions = ChatSession.query.filter_by(user_id=student_id).order_by(ChatSession.updated_at.desc()).all()
    
    result = []
    for session in sessions:
        last_message = session.messages[-1].content if session.messages else ''
        result.append({
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'last_message': last_message[:50] + '...' if len(last_message) > 50 else last_message,
            'message_count': len(session.messages)
        })
    
    return jsonify({
        'student': {
            'id': student.id,
            'username': student.username,
            'display_name': student.display_name
        },
        'sessions': result
    })


@bp.route('/teacher/students/<int:student_id>/chat-sessions/<int:session_id>/messages', methods=['GET'])
@teacher_required
def get_student_chat_messages(student_id, session_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'success': False, 'message': '只能查看学生的聊天记录'}), 400
    
    session = ChatSession.query.filter_by(id=session_id, user_id=student_id).first_or_404()
    
    messages = []
    for msg in session.messages:
        images = []
        if msg.images:
            try:
                image_list = json.loads(msg.images)
                images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
            except:
                pass
        
        messages.append({
            'id': msg.id,
            'role': msg.role,
            'content': msg.content,
            'stdout': msg.stdout,
            'stderr': msg.stderr,
            'images': images,
            'created_at': msg.created_at.isoformat()
        })
    
    return jsonify({
        'session': {
            'id': session.id,
            'title': session.title,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat()
        },
        'messages': messages
    })
