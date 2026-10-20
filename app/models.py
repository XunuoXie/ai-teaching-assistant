
from datetime import datetime
from .extensions import db


class Class(db.Model):
    __tablename__ = 'class_table'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    display_name = db.Column(db.String(80), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default='student')


class StudentClass(db.Model):
    __tablename__ = 'student_class'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class_table.id'))
    joined_at = db.Column(db.DateTime, default=datetime.now)


class Assignment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    deadline = db.Column(db.DateTime)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    class_id = db.Column(db.Integer, db.ForeignKey('class_table.id'))
    created_at = db.Column(db.DateTime, default=datetime.now)
    total_score = db.Column(db.Integer, default=100)
    
    def get_deadline_str(self):
        return self.deadline.strftime('%Y-%m-%d %H:%M') if self.deadline else '无截止时间'
    
    def get_deadline_datetime_str(self):
        return self.deadline.strftime('%Y-%m-%dT%H:%M') if self.deadline else ''
    
    def is_deadline_urgent(self):
        if not self.deadline:
            return False
        return self.deadline < datetime.now()
        
    def is_past_deadline(self):
        if not self.deadline:
            return False
        return datetime.now() > self.deadline


class Submission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    assignment_id = db.Column(db.Integer, db.ForeignKey('assignment.id'))
    student_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    code = db.Column(db.Text)
    stdout = db.Column(db.Text)
    stderr = db.Column(db.Text)
    images = db.Column(db.Text)
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    score = db.Column(db.Integer)
    feedback = db.Column(db.Text)


class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), default='新对话')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now)
    
    messages = db.relationship('ChatMessage', backref='session', cascade='all, delete-orphan', order_by='ChatMessage.created_at')


class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('chat_session.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    stdout = db.Column(db.Text)
    stderr = db.Column(db.Text)
    images = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.now)


class XuexitongStudent(db.Model):
    __tablename__ = 'xuexitong_student'
    id = db.Column(db.Integer, primary_key=True)
    cpi = db.Column(db.String(100), unique=True, nullable=False, index=True)
    course_id = db.Column(db.String(50), nullable=False)
    clazz_id = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    student_id = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship('User', backref=db.backref('xuexitong_binding', uselist=False))
