
import os
import shutil
import subprocess
import logging
from urllib.parse import urlparse, parse_qs
from flask import Flask, redirect, url_for, session, send_from_directory, request
from flask_cors import CORS
from .config import Config
from .extensions import db
from .models import User, Assignment, Submission, Class, StudentClass
from .routes import auth as auth_bp
from .routes import student as student_bp
from .routes import teacher as teacher_bp
from .routes import api as api_bp
from .routes import api_auth as api_auth_bp
from .routes import xuetang as xuetang_bp
import os


def ensure_packages():
    """安装必要的Python包"""
    packages = ['matplotlib', 'numpy', 'pillow']
    missing = []
    for pkg in packages:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        try:
            subprocess.check_call([
                os.sys.executable, '-m', 'pip', 'install', *missing
            ])
        except Exception as e:
            print(f"Failed to install packages: {e}")


def _parse_xuetang_referer():
    """从 Referer 头中解析学习通参数并存入 session"""
    referer = request.headers.get('Referer', '')
    if 'xuexitong.com' not in referer and 'xuetang' not in referer.lower():
        return

    parsed = urlparse(referer)
    params = parse_qs(parsed.query)
    cpi = params.get('cpi', [None])[0]
    course_id = params.get('courseId', [None])[0]
    clazz_id = params.get('clazzId', [None])[0]

    if cpi:
        session['xuetang_params'] = {
            'cpi': cpi,
            'courseId': course_id,
            'clazzId': clazz_id
        }
        session.modified = True


def create_app(config_class=Config):
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(__name__, static_folder=os.path.join(base_dir, 'static'))
    app.config.from_object(config_class)
    
    Config.init_app(app)
    
    logging.basicConfig(level=logging.INFO)
    
    db.init_app(app)
    CORS(app, supports_credentials=True, expose_headers=['Authorization'], allow_headers=['Content-Type', 'Authorization'])
    
    with app.app_context():
        db.create_all()
        
        ensure_packages()
        
        if User.query.count() == 0:
            from werkzeug.security import generate_password_hash
            
            admin = User(
                username='admin',
                display_name='管理员',
                password=generate_password_hash('admin123'),
                role='admin'
            )
            teacher = User(
                username='teacher',
                display_name='张老师',
                password=generate_password_hash('teacher123'),
                role='teacher'
            )
            student1 = User(
                username='student1',
                display_name='李同学',
                password=generate_password_hash('student123'),
                role='student'
            )
            student2 = User(
                username='student2',
                display_name='王同学',
                password=generate_password_hash('student123'),
                role='student'
            )
            
            db.session.add_all([admin, teacher, student1, student2])
            db.session.commit()
            print("✅ 已创建演示账户！")
            print("   - 管理员: admin / admin123")
            print("   - 教师: teacher / teacher123")
            print("   - 学生: student1 / student123")
            print("   - 学生: student2 / student123")
    
    app.register_blueprint(auth_bp.bp)
    app.register_blueprint(student_bp.bp)
    app.register_blueprint(teacher_bp.bp)
    app.register_blueprint(api_bp.bp, url_prefix='/api')
    app.register_blueprint(api_auth_bp.bp, url_prefix='/api/auth')
    app.register_blueprint(xuetang_bp.bp)
    
    @app.context_processor
    def inject_user():
        return dict(User=User, request=request)
    
    @app.route('/')
    def index():
        frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
        if os.path.exists(os.path.join(frontend_dist, 'index.html')):
            return send_from_directory(frontend_dist, 'index.html')
        return "<h1>Vue frontend not built yet. Please run 'npm install && npm run build' in the frontend directory.</h1>"

    @app.route('/xuetang-entry')
    def xuetang_entry():
        _parse_xuetang_referer()
        # Build redirect URL with query params for cross-origin support
        xuetang_params = session.get('xuetang_params', {})
        params = {}
        if xuetang_params.get('cpi'):
            params['cpi'] = xuetang_params['cpi']
        if xuetang_params.get('courseId'):
            params['courseId'] = xuetang_params['courseId']
        if xuetang_params.get('clazzId'):
            params['clazzId'] = xuetang_params['clazzId']

        if params:
            import urllib.parse
            qs = urllib.parse.urlencode(params)
            target = f'/xuetang?{qs}'
        else:
            target = '/xuetang'

        frontend_url = os.environ.get('FRONTEND_URL', '')
        return redirect(f'{frontend_url}{target}')

    @app.route('/<path:path>')
    def serve_static(path):
        frontend_dist = os.path.join(base_dir, 'frontend', 'dist')
        if path and os.path.exists(os.path.join(frontend_dist, path)):
            return send_from_directory(frontend_dist, path)
        if path.startswith('api/'):
            return "API route not found", 404
        if os.path.exists(os.path.join(frontend_dist, 'index.html')):
            return send_from_directory(frontend_dist, 'index.html')
        return "<h1>Page not found</h1>", 404
    
    os.makedirs(app.config['OUTPUT_DIR'], exist_ok=True)
    os.makedirs(app.config['SANDBOX_BASE'], exist_ok=True)
    
    return app
