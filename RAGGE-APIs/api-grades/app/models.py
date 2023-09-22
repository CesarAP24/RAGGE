from flask_sqlalchemy import SQLAlchemy
from config.local import config
import uuid
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
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


def generate_code_homework():
    return str(random.randint(000, 999)).zfill(3)


class Homework(db.Model):
    __tablename__ = 'homeworks'
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    name_homework = db.Column(db.String(200), nullable=False, unique=True)
    id_course = db.Column(db.String(36), ForeignKey(
        'course.id'), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False,
                         unique=True, default=datetime.utcnow)
    indications = db.Column(db.String(1000), nullable=False, unique=True)
    id_teacher = db.Column(db.string(36), db.ForeignKey(
        'teacher.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)


def __int__(self, name_homework, id_course, id_teacher, deadline, indications, created_at):
    self.name_homework = name_homework
    self.id_course = id_course
    self.id_teacher = id_teacher
    self.deadline = deadline
    self.indicates = indicators
    self.created_at = created_at


def __repr__(self):
    return "<Homework %r" % self.name_homework


def serialize(self):
    return {
        "id": self.id
        "name_homework": self.name_homework,
        "id_course": self.id_course,
        "id_teacher": self.id_teacher,
        "indicates": self.indicates,
        "deadline": self.deadline.strftime('%Y-%m-%d %H:%M:%S'),
    }


class Delivery(db.Model):
    __tablename__ = 'deliveries'
    date = db.Column(db.DateTime, nullable=False)
    id_homework = db.Column(db.String(36), ForeignKey(
        'homework.id'), nullable=False)
    id_teacher = db.Column(db.String(36), ForeignKey(
        'teacher.id'), nullable=False)
    id_student = db.Column(db.String(36), ForeignKey(
        'student.id'), nullable=False)
    id_couser = db.Column(db.String(36), ForeignKey(
        'course.id'), nullable=False)
    route_archive = db.Column(
        db.String(200), nullable=False, unique=True, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)


def __init__(self, date, id_homework, id_teacher, id_student, id_student, route_archive, created_at):
    self.date = date
    self.id_homework = id_homework
    self.id_teacher = id_teacher
    self.id_student = id_student
    self.id_student = id_student
    self.route_archive = route_archive
    self.created_at = datetime.utcnow()


def __repr__(self):
    return '<Delivery %r>' % self.date


def serialize(self):
    return {
        "id": self.id
        "date": self.date,
        "id_homework": self.id_homework,
        "id_teacher": self.id_teacher,
        "id_student": self.id_student,
        "id_course": self.id_course,
        "route_archive": self.route_archive,
    }


class Score(db.Model):
     __tablename__ = 'scores'
    date = db.Column(db.DateTime, nullable=False)
    id_homework = db.Column(db.String(36), ForeignKey('homework.id'), nullable=False)
    id_teacher = db.Column(db.String(36), ForeignKey('teacher.id'), nullable=False)
    id_student = db.Column(db.String(36), ForeignKey('student.id'), nullable=False)
    id_couser = db.Column(db.String(36), ForeignKey('course.id'), nullable=False)
    value = db.Column(db.Integer(20), nullbale=False, unique=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

def __init__(self, date, id_homework, id_teacher, id_student, value, created_at):
    self.date = date
    self.id_homework = id_homework
    self.id_teacher = id_teacher
    self.id_student = id_student
    self.id_course = id_course
    self.value = value
    self.created_at = datetime.utcnow()

def __repr__(self):
    return '<Score %r>' % self.date

def serialize(self):
    return {
        "id": self.id
        "date": self.date,
        "id_teacher": self.id_teacher,
        "id_student": self.id_student,
        "id_course": self.id_course,
        "value": self.value,
    }


