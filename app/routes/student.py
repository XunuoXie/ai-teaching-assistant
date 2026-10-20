from flask import Blueprint, render_template, session, redirect, url_for, request, jsonify, url_for
from datetime import datetime
from ..models import User, Assignment, Submission, StudentClass, Class
from ..extensions import db
from ..utils import require_role
from ..utils.code_executor import execute_python_code
from ..utils.security import is_safe_code
import json

bp = Blueprint('student', __name__)


@bp.route('/student')
@require_role('student')
def dashboard():
    user = User.query.get(session['user_id'])
    class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=user.id).all()]
    assignments = Assignment.query.filter(
        (Assignment.class_id == None) | 
        (Assignment.class_id.in_(class_ids))
    ).order_by(Assignment.created_at.desc()).all()
    
    submissions = Submission.query.filter_by(student_id=user.id).all()
    sub_map = {s.assignment_id: s for s in submissions}
    
    classes = Class.query.all()
    class_map = {c.id: c.name for c in classes}
    
    return render_template('student/dashboard.html', 
                          assignments=assignments, 
                          submissions=submissions,
                          submission_map=sub_map, 
                          user=user,
                          now=datetime.now(),
                          class_map=class_map,
                          display_name=user.display_name)


@bp.route('/student/assignment/<int:aid>')
@require_role('student')
def assignment_detail(aid):
    user = User.query.get(session['user_id'])
    class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=user.id).all()]
    
    assignment = Assignment.query.get_or_404(aid)
    
    if assignment.class_id:
        student_in_class = StudentClass.query.filter_by(
            student_id=user.id,
            class_id=assignment.class_id
        ).first()
        if not student_in_class:
            return "无权访问", 403
    
    submission = Submission.query.filter_by(
        assignment_id=aid,
        student_id=user.id
    ).first()
    
    images = []
    if submission and submission.images:
        try:
            image_list = json.loads(submission.images)
            images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
        except:
            pass
    
    classes = Class.query.all()
    class_map = {c.id: c.name for c in classes}
    
    return render_template('student/assignment.html',
                          assignment=assignment,
                          submission=submission,
                          images=images,
                          class_map=class_map,
                          display_name=user.display_name)


@bp.route('/student/run_code', methods=['POST'])
@require_role('student')
def run_code():
    data = request.json
    code = data.get('code', '')
    
    if not code:
        return jsonify({'error': '代码为空'}), 400
    
    if not is_safe_code(code):
        return jsonify({'error': '代码包含不安全操作'}), 400
    
    stdout, stderr, images = execute_python_code(code)
    
    image_urls = []
    for img in images:
        image_urls.append(url_for('static', filename=f'outputs/{img}'))
    
    return jsonify({
        'stdout': stdout,
        'stderr': stderr,
        'images': image_urls
    })


@bp.route('/student/submit_assignment/<int:aid>', methods=['POST'])
@require_role('student')
def submit_assignment(aid):
    user = User.query.get(session['user_id'])
    class_ids = [sc.class_id for sc in StudentClass.query.filter_by(student_id=user.id).all()]
    
    assignment = Assignment.query.get_or_404(aid)
    
    if assignment.class_id:
        student_in_class = StudentClass.query.filter_by(
            student_id=user.id,
            class_id=assignment.class_id
        ).first()
        if not student_in_class:
            return jsonify({'error': '无权访问'}), 403
    
    data = request.json
    code = data.get('code', '')
    
    from datetime import datetime
    if assignment.deadline and datetime.now() > assignment.deadline:
        return jsonify({'error': '作业已经截止，无法提交'}), 403
    
    if not is_safe_code(code):
        return jsonify({'error': '代码包含不安全操作'}), 400
    
    stdout, stderr, images = execute_python_code(code)
    
    image_str = json.dumps(images)
    
    submission = Submission.query.filter_by(
        assignment_id=aid,
        student_id=user.id
    ).order_by(Submission.submitted_at.desc()).first()
    
    if submission:
        submission.code = code
        submission.stdout = stdout
        submission.stderr = stderr
        submission.images = image_str
        from datetime import datetime
        submission.submitted_at = datetime.now()
    else:
        submission = Submission(
            assignment_id=aid,
            student_id=user.id,
            code=code,
            stdout=stdout,
            stderr=stderr,
            images=image_str
        )
        db.session.add(submission)
    
    db.session.commit()
    
    image_urls = []
    for img in images:
        image_urls.append(url_for('static', filename=f'outputs/{img}'))
    
    return jsonify({
        'success': True,
        'stdout': stdout,
        'stderr': stderr,
        'images': image_urls
    })


@bp.route('/chat')
@require_role('student')
def chat():
    user = User.query.get(session['user_id'])
    return render_template('chat.html', display_name=user.display_name)

