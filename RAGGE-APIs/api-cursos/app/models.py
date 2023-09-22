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
    return random.randit(0000, 9999)


class Course(db.Model):
    __tablename__ = 'courses'
    id_course = db.Column(db.Integer, primary_key=True, default=generate_random_code)
    course_name = db.Column(db.String(100), nullable=False, unique=True)
    id_teacher = db.Column(db.String(36), ForeignKey('teacher.id'), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return '<Course %r>' % self.course_name
    
    def serialize(self):
        return {
            "id": self.id,
            "course_name": self.course_name,
            "id_teacher": self.id_teacher,
            "id_student": self.id_student,
        }
