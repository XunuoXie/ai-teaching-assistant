from flask import Blueprint, render_template, session, request, redirect, url_for, jsonify
from datetime import datetime
from ..models import User, Assignment, Submission, StudentClass, Class
from ..extensions import db
from ..utils import require_role
from ..utils.code_executor import execute_python_code
from ..utils.security import is_safe_code
from werkzeug.security import generate_password_hash

bp = Blueprint('teacher', __name__)


@bp.route('/teacher')
@require_role('teacher')
def dashboard():
    total_assignments = Assignment.query.count()
    total_students = User.query.filter_by(role='student').count()
    unscored_submissions = Submission.query.filter(Submission.score == None).count()
    scored_submissions = Submission.query.filter(Submission.score != None).count()
    
    return render_template('teacher/dashboard.html', 
                         display_name=session['display_name'],
                         total_assignments=total_assignments,
                         total_students=total_students,
                         unscored_submissions=unscored_submissions,
                         scored_submissions=scored_submissions)


@bp.route('/teacher/assignments')
@require_role('teacher')
def assignments():
    assignments = Assignment.query.order_by(Assignment.created_at.desc()).all()
    classes = Class.query.all()
    class_map = {c.id: c.name for c in classes}
    return render_template('teacher/assignments.html', assignments=assignments,
                          display_name=session['display_name'],
                          class_map=class_map)


@bp.route('/teacher/assignment/new', methods=['GET', 'POST'])
@require_role('teacher')
def new_assignment():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        deadline_str = request.form.get('deadline')
        class_id = request.form.get('class_id')
        
        deadline = None
        if deadline_str:
            deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        
        class_id = int(class_id) if class_id else None
        
        assignment = Assignment(
            title=title,
            description=description,
            deadline=deadline,
            class_id=class_id,
            created_by=session['user_id']
        )
        
        db.session.add(assignment)
        db.session.commit()
        return redirect(url_for('teacher.assignments'))
    
    classes = Class.query.all()
    return render_template('teacher/create_assignment.html',
                          display_name=session['display_name'],
                          classes=classes)


@bp.route('/teacher/assignment/<int:aid>/edit', methods=['GET', 'POST'])
@require_role('teacher')
def edit_assignment(aid):
    assignment = Assignment.query.get_or_404(aid)
    
    if request.method == 'POST':
        assignment.title = request.form['title']
        assignment.description = request.form['description']
        deadline_str = request.form.get('deadline')
        class_id = request.form.get('class_id')
        
        if deadline_str:
            assignment.deadline = datetime.strptime(deadline_str, '%Y-%m-%dT%H:%M')
        else:
            assignment.deadline = None
        
        assignment.class_id = int(class_id) if class_id else None
        
        db.session.commit()
        return redirect(url_for('teacher.assignments'))
    
    classes = Class.query.all()
    return render_template('teacher/edit_assignment.html',
                          assignment=assignment,
                          display_name=session['display_name'],
                          classes=classes)


@bp.route('/teacher/assignment/<int:aid>/delete', methods=['POST'])
@require_role('teacher')
def delete_assignment(aid):
    assignment = Assignment.query.get_or_404(aid)
    Submission.query.filter_by(assignment_id=aid).delete()
    db.session.delete(assignment)
    db.session.commit()
    return redirect(url_for('teacher.assignments'))


@bp.route('/teacher/submissions')
@require_role('teacher')
def submissions():
    assignment_id = request.args.get('assignment_id')
    class_id = request.args.get('class_id')
    
    # 获取所有班级
    classes = Class.query.all()
    
    # 筛选提交记录
    query = Submission.query
    
    if assignment_id:
        query = query.filter_by(assignment_id=assignment_id)
    
    if class_id:
        # 需要通过作业关联到班级
        assignment_ids = [a.id for a in Assignment.query.filter_by(class_id=class_id).all()]
        if assignment_ids:
            query = query.filter(Submission.assignment_id.in_(assignment_ids))
        else:
            # 没有指定班级的作业
            query = query.filter_by(id=0)  # 空结果
    
    submissions = query.all()
    
    assignments = Assignment.query.all()
    students = User.query.filter_by(role='student').all()
    
    # 如果选择了班级，也筛选作业列表
    filtered_assignments = assignments
    if class_id:
        filtered_assignments = [a for a in assignments if a.class_id == int(class_id)]
    
    student_map = {s.id: s.display_name for s in students}
    assignment_map = {a.id: a.title for a in assignments}
    
    unsubmitted_students = []
    assignment_unsubmitted_stats = []
    
    if assignment_id:
        assignment = Assignment.query.get(assignment_id)
        if assignment:
            student_ids = set()
            
            if assignment.class_id:
                student_classes = StudentClass.query.filter_by(class_id=assignment.class_id).all()
                student_ids = {sc.student_id for sc in student_classes}
            else:
                student_ids = {s.id for s in students}
            
            submitted_ids = {s.student_id for s in submissions}
            unsubmitted_ids = student_ids - submitted_ids
            unsubmitted_students = [s for s in students if s.id in unsubmitted_ids]
    else:
        # 根据班级筛选统计
        stats_assignments = filtered_assignments if class_id else assignments
        for assignment in stats_assignments:
            assignment_submissions = Submission.query.filter_by(assignment_id=assignment.id).all()
            submitted_ids = {s.student_id for s in assignment_submissions}
            
            student_ids = set()
            if assignment.class_id:
                student_classes = StudentClass.query.filter_by(class_id=assignment.class_id).all()
                student_ids = {sc.student_id for sc in student_classes}
            else:
                student_ids = {s.id for s in students}
            
            total_required = len(student_ids)
            unsubmitted_count = total_required - len(submitted_ids)
            
            assignment_unsubmitted_stats.append({
                'id': assignment.id,
                'title': assignment.title,
                'total': total_required,
                'submitted': len(submitted_ids),
                'unsubmitted': unsubmitted_count
            })
    
    return render_template('teacher/submissions.html',
                          submissions=submissions,
                          assignments=assignments,
                          classes=classes,
                          student_map=student_map,
                          assignment_map=assignment_map,
                          selected_assignment=assignment_id,
                          selected_class=class_id,
                          display_name=session['display_name'],
                          total_submissions=len(submissions),
                          scored_count=sum(1 for s in submissions if s.score),
                          unscored_count=sum(1 for s in submissions if not s.score),
                          unsubmitted_students=unsubmitted_students,
                          assignment_unsubmitted_stats=assignment_unsubmitted_stats)


@bp.route('/teacher/submission/<int:sid>')
@require_role('teacher')
def view_submission(sid):
    submission = Submission.query.get_or_404(sid)
    student = User.query.get(submission.student_id)
    assignment = Assignment.query.get(submission.assignment_id)
    import json
    from flask import url_for
    images = []
    if submission.images:
        try:
            image_list = json.loads(submission.images)
            images = [url_for('static', filename=f'outputs/{img}') for img in image_list]
        except:
            pass
    return render_template('teacher/view_submission.html',
                          submission=submission,
                          student=student,
                          assignment=assignment,
                          images=images,
                          display_name=session['display_name'])


@bp.route('/teacher/submission/<int:sid>/grade', methods=['POST'])
@require_role('teacher')
def grade_submission(sid):
    submission = Submission.query.get_or_404(sid)
    score_str = request.form.get('score', '')
    if score_str.strip():
        submission.score = int(score_str)
    submission.feedback = request.form.get('feedback', '')
    db.session.commit()
    return redirect(url_for('teacher.view_submission', sid=sid))


@bp.route('/teacher/run_student_code', methods=['POST'])
@require_role('teacher')
def run_student_code():
    data = request.json
    code = data.get('code', '')
    
    if not code:
        return jsonify({'stdout': '', 'stderr': '请输入代码'})
    
    if not is_safe_code(code):
        return jsonify({'stdout': '', 'stderr': '检测到不安全代码，禁止运行'})
    
    stdout, stderr, images = execute_python_code(code)
    
    image_urls = []
    if images:
        from flask import url_for
        image_urls = [url_for('static', filename=f'outputs/{img}') for img in images]
    
    return jsonify({'stdout': stdout, 'stderr': stderr, 'images': image_urls})


@bp.route('/teacher/classes')
@require_role('teacher')
def classes():
    classes = Class.query.all()
    return render_template('teacher/classes.html',
                          classes=classes,
                          display_name=session['display_name'])


@bp.route('/teacher/class/create', methods=['GET', 'POST'])
@require_role('teacher')
def create_class():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        cls = Class(
            name=name,
            description=description,
            created_by=session['user_id']
        )
        db.session.add(cls)
        db.session.commit()
        return redirect(url_for('teacher.classes'))
    return render_template('teacher/create_class.html', display_name=session['display_name'])


@bp.route('/teacher/class/edit/<int:class_id>', methods=['GET', 'POST'])
@require_role('teacher')
def edit_class(class_id):
    cls = Class.query.get_or_404(class_id)
    if request.method == 'POST':
        cls.name = request.form['name']
        cls.description = request.form.get('description', '')
        db.session.commit()
        return redirect(url_for('teacher.classes'))
    return render_template('teacher/edit_class.html',
                          cls=cls, display_name=session['display_name'])


@bp.route('/teacher/class/delete/<int:class_id>', methods=['POST'])
@require_role('teacher')
def delete_class(class_id):
    cls = Class.query.get_or_404(class_id)
    StudentClass.query.filter_by(class_id=class_id).delete()
    Assignment.query.filter_by(class_id=class_id).update({'class_id': None})
    db.session.delete(cls)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/teacher/class/<int:class_id>/students')
@require_role('teacher')
def class_students(class_id):
    cls = Class.query.get_or_404(class_id)
    class_students = db.session.query(User).join(StudentClass).filter(StudentClass.class_id == class_id).all()
    all_students = User.query.filter_by(role='student').all()
    student_ids_in_class = {s.id for s in class_students}
    available_students = [s for s in all_students if s.id not in student_ids_in_class]
    return render_template('teacher/class_students.html',
                          cls=cls,
                          class_students=class_students,
                          available_students=available_students,
                          display_name=session['display_name'])


@bp.route('/teacher/class/<int:class_id>/add_student', methods=['POST'])
@require_role('teacher')
def add_student_to_class(class_id):
    student_id = request.form.get('student_id')
    if student_id:
        exists = StudentClass.query.filter_by(class_id=class_id, student_id=student_id).first()
        if not exists:
            sc = StudentClass(class_id=class_id, student_id=student_id)
            db.session.add(sc)
            db.session.commit()
    return redirect(url_for('teacher.class_students', class_id=class_id))


@bp.route('/teacher/class/<int:class_id>/remove_student/<int:student_id>', methods=['POST'])
@require_role('teacher')
def remove_student_from_class(class_id, student_id):
    sc = StudentClass.query.filter_by(class_id=class_id, student_id=student_id).first()
    if sc:
        db.session.delete(sc)
        db.session.commit()
    return redirect(url_for('teacher.class_students', class_id=class_id))


@bp.route('/teacher/students')
@require_role('teacher')
def students():
    students = User.query.filter_by(role='student').all()
    classes = Class.query.all()
    
    student_class_map = {}
    for student in students:
        student_classes = StudentClass.query.filter_by(student_id=student.id).all()
        class_ids = [sc.class_id for sc in student_classes]
        student_class_list = [c for c in classes if c.id in class_ids]
        student_class_map[student.id] = student_class_list
    
    return render_template('teacher/students.html',
                          students=students,
                          classes=classes,
                          student_class_map=student_class_map,
                          display_name=session['display_name'])


@bp.route('/teacher/student/new', methods=['POST'])
@require_role('teacher')
def new_student():
    username = request.form['username']
    display_name = request.form['display_name']
    password = request.form['password']
    
    if User.query.filter_by(username=username).first():
        return "用户名已存在", 400
    
    hashed = generate_password_hash(password)
    user = User(username=username, display_name=display_name, password=hashed, role='student')
    db.session.add(user)
    db.session.commit()
    return redirect(url_for('teacher.students'))


@bp.route('/teacher/add_student', methods=['POST'])
@require_role('teacher')
def add_student():
    data = request.json
    display_name = data.get('display_name')
    password = data.get('password')
    
    if not display_name or not password:
        return jsonify({'success': False, 'error': '姓名和密码不能为空'})
    
    from werkzeug.security import generate_password_hash
    import uuid
    hashed = generate_password_hash(password)
    # 临时分配一个用户名
    temp_username = f"temp_{uuid.uuid4().hex[:8]}"
    user = User(username=temp_username, display_name=display_name, password=hashed, role='student')
    db.session.add(user)
    db.session.commit()
    
    # 将学号自动设置为用户名
    user.username = str(user.id)
    db.session.commit()
    
    return jsonify({'success': True})


@bp.route('/teacher/student/<int:student_id>')
@require_role('teacher')
def student_detail(student_id):
    student = User.query.get_or_404(student_id)
    assignments = Assignment.query.all()
    all_classes = Class.query.all()
    
    student_classes = StudentClass.query.filter_by(student_id=student_id).all()
    student_class_ids = {sc.class_id for sc in student_classes}
    student_class_list = [c for c in all_classes if c.id in student_class_ids]
    
    available_classes = [c for c in all_classes if c.id not in student_class_ids]
    
    student_assignments = []
    for assignment in assignments:
        submission = Submission.query.filter_by(
            assignment_id=assignment.id,
            student_id=student_id
        ).first()
        student_assignments.append({
            'id': assignment.id,
            'title': assignment.title,
            'submitted': submission is not None,
            'scored': submission is not None and submission.score is not None,
            'score': submission.score if submission else None
        })
    
    return jsonify({
        'id': student.id,
        'username': student.username,
        'display_name': student.display_name,
        'assignments': student_assignments,
        'classes': [{'id': c.id, 'name': c.name} for c in student_class_list],
        'available_classes': [{'id': c.id, 'name': c.name} for c in available_classes]
    })


@bp.route('/teacher/student/<int:student_id>/add_class', methods=['POST'])
@require_role('teacher')
def add_class_to_student(student_id):
    data = request.json
    class_id = data.get('class_id')
    if not class_id:
        return jsonify({'success': False, 'error': '缺少班级ID'})
    if StudentClass.query.filter_by(student_id=student_id, class_id=class_id).first():
        return jsonify({'success': False, 'error': '学生已在该班级中'})
    sc = StudentClass(student_id=student_id, class_id=class_id)
    db.session.add(sc)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/teacher/student/<int:student_id>/remove_class', methods=['POST'])
@require_role('teacher')
def remove_class_from_student(student_id):
    data = request.json
    class_id = data.get('class_id')
    if not class_id:
        return jsonify({'success': False, 'error': '缺少班级ID'})
    StudentClass.query.filter_by(student_id=student_id, class_id=class_id).delete()
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/teacher/delete_student/<int:student_id>', methods=['POST'])
@require_role('teacher')
def delete_student(student_id):
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        return jsonify({'success': False, 'error': '只能删除学生用户'})
    
    StudentClass.query.filter_by(student_id=student_id).delete()
    Submission.query.filter_by(student_id=student_id).delete()
    db.session.delete(student)
    db.session.commit()
    return jsonify({'success': True})


@bp.route('/teacher/student/<int:sid>/delete', methods=['POST'])
@require_role('teacher')
def delete_student_old(sid):
    student = User.query.get_or_404(sid)
    Submission.query.filter_by(student_id=sid).delete()
    StudentClass.query.filter_by(student_id=sid).delete()
    db.session.delete(student)
    db.session.commit()
    return redirect(url_for('teacher.students'))
