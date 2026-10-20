import logging
from flask import current_app
from ..models import User, Class, StudentClass
from ..extensions import db

logger = logging.getLogger(__name__)


def auto_assign_student(student_id):
    """将学生自动添加到默认教师的默认班级。

    从配置读取 DEFAULT_TEACHER_USERNAME，找到对应的教师，
    获取或创建其默认班级，然后将学生加入该班级。
    如果未配置 DEFAULT_TEACHER_USERNAME，则静默跳过。
    """
    teacher_username = current_app.config.get('DEFAULT_TEACHER_USERNAME', '')
    if not teacher_username:
        return

    teacher = User.query.filter_by(username=teacher_username, role='teacher').first()
    if not teacher:
        logger.warning('默认教师 %s 不存在或不是教师角色，跳过自动分班', teacher_username)
        return

    default_class = Class.query.filter_by(created_by=teacher.id).first()
    if not default_class:
        default_class = Class(
            name=f'{teacher.display_name}的班级',
            description='默认班级（自动创建）',
            created_by=teacher.id
        )
        db.session.add(default_class)
        db.session.flush()

    existing = StudentClass.query.filter_by(
        class_id=default_class.id,
        student_id=student_id
    ).first()
    if existing:
        return

    sc = StudentClass(class_id=default_class.id, student_id=student_id)
    db.session.add(sc)
    db.session.commit()
