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
    return random.randint(0000, 9999)


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(30), nullable=False,
                          unique=False, default=False)
    dni = db.Column(db.String(20), nullable=False, unique=True, default=False)
    email = db.Column(db.String(99), nullable=False,
                      unique=True, default=False)
    contrasena = db.Column(db.String(255), nullable=False, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return '<User %r>' % self.firstname

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "dni": self.dni,
            "email": self.email,
            "contrasena": self.contrasena
        }

class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.String(36), ForeignKey('users.id'), primary_key=True)
    phone_number = db.Column(
        db.String(50), nullable=False, unique=True, default=False)

    def __repr__(self):
        return '<Teacher %r>' % self.firstname

    def serialize(self):
        return {
            "id": self.id,
            "phone_number": self.phone_number
        }


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.String(36), ForeignKey('users.id'), primary_key=True)

    def __repr__(self):
        return '<Student %r>' % self.id

    def serialize(self):
        return {
            "id": self.id
        }


class Course(db.Model):
    __tablename__ = 'courses'
    id_course = db.Column(db.Integer, primary_key=True,
                          default=lambda: generate_random_code())
    course_name = db.Column(db.String(100), nullable=False, unique=True)
    id_teacher = db.Column(db.String(36), ForeignKey(
        'teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __repr__(self):
        return '<Course %r>' % self.course_name

    def serialize(self):
        return {
            "id_course": self.id_course,
            "course_name": self.course_name,
            "id_teacher": self.id_teacher,
        }


class ATieneC(db.Model):
    __tablename__ = 'atienec'
    id_alumno = db.Column(db.String(36), ForeignKey('students.id'), primary_key=True)
    id_curso = db.Column(db.Integer, ForeignKey('courses.id_course'), primary_key=True)

    def serialize(self):
        return {
            "id_alumno": self.id_alumno,
            "id_curso": self.id_curso
        }

class Homework(db.Model):
    __tablename__ = 'homeworks'
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    id_course = db.Column(db.Integer, ForeignKey(
        'courses.id_course'), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    deadline = db.Column(db.DateTime, nullable=False,
                         unique=True, default=datetime.utcnow)
    indications = db.Column(db.String(1000), nullable=False, unique=False)
    id_teacher = db.Column(db.String(36), db.ForeignKey(
        'teachers.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def serialize(self):
        return {
            "id": self.id,
            "id_course": self.id_course,
            "name": self.name,
            "deadline": self.deadline,
            "indications": self.indications,
            "id_teacher": self.id_teacher
        }

class Score(db.Model):
    __tablename__ = 'scores'

    date = db.Column(db.DateTime, nullable=False, primary_key=True, default=lambda: datetime.utcnow())
    id_homework = db.Column(db.String(36), ForeignKey('homeworks.id'), primary_key=True, unique=False)
    
    id_course = db.Column(db.Integer, ForeignKey('courses.id_course'), unique=False, nullable=False)
    value = db.Column(db.Integer, nullable=False)
    id_student = db.Column(db.String(36), ForeignKey('students.id'), nullable=False)
    id_teacher = db.Column(db.String(36), ForeignKey('teachers.id'), nullable=False)

    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def serialize(self):
        return {
            "date": self.date,
            "id_homework": self.id_homework,
            "id_course": self.id_course,
            "value": self.value,
            "id_student": self.id_student,
            "id_teacher": self.id_teacher
        }
