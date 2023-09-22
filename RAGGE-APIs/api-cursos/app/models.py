from flask_sqlalchemy import SQLAlchemy
from config.local import config
import uuid
import random
from datetime import datetime
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import sys


db = SQLAlchemy()


def setup_db(app, database_path):
    app.config["SQLALCHEMY_DATABASE_URI"] = config['DATABASE_URI'] if database_path is None else database_path
    db.app = app
    db.init_app(app)
    db.create_all()

# Models


def generate_random_code():
    return str(random.randit(0000, 9999))


class Course(db.Model):
    __tablename__ = 'courses'
    id_course = db.Column(db.String(4), primary_key=True,
                          default=generate_random_code)
    course_name = db.Column(db.String(100), nullable=False, unique=True)
    id_teacher = db.Column(db.String(36), ForeignKey(
        'teacher.id'), nullable=False)
    id_student = db.Column(db.String(36), ForeignKey(
        'student.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)


def __init__(self, course_name, id_teacher, id_student, created_at):
    self.course_name = course_name
    self.id_teacher = id_teacher
    self.id_student = id_student
    self.created_at = datetime.utcnow()


def __repr__(self):
    return '<Course %r>' % self.course_name


def serialize(self):
    return {
        "id": self.id
        "course_name": self.course_name,
        "id_teacher": self.id_teacher,
        "id_student": self.id_student,
    }
