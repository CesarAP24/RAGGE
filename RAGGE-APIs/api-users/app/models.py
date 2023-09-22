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


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    firstname = db.Column(db.String(30), nullable=False,
                          unique=False, default=False)
    lastname = db.Column(db.String(60), nullable=False,
                         unique=True, default=False)
    dni = db.Column(db.String(20), nullable=False, unique=True, default=False)
    email = db.Column(db.String(99), nullable=False,
                      unique=True, default=False)
    contrasena = db.Column(db.String(255), nullable=False,
                           unique=True, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)


def __init__(self, firstname, lastname, dni, email, contrasena, created_at):
    self.firstname = firstname
    self.lastname = lastname
    self.dni = dni
    self.email = email
    self.contrasena = contrasena
    self.created_at = created_at


def __repr__(self):
    return '<User %r>' % self.firstname


def serialize(self):
    return {
        "id": self.id
        "firstname": self.firstname
        "lastname": self.lastname
        "dni": self.dni
        "email": self.email
        "contrasena": self.contrasena
    }


class Teacher(db.Model):
    __tablename__ = 'teachers'
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    firstname = db.Column(db.String(30), nullable=False,
                          unique=False, default=False)
    lastname = db.Column(db.String(60), nullable=False,
                         unique=True, default=False)
    dni = db.Column(db.String(20), nullable=False, unique=True, default=False)
    email = db.Column(db.String(99), nullable=False,
                      unique=True, default=False)
    phone_number = db.Column(
        db.String(50, nullable=False, unique=True, default=False))
    contrasena = db.Column(db.String(255), nullable=False,
                           unique=True, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)

    def __init__(self, firstname, lastname, email, phone_number, contrasena, created_at):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.phone_number = phone_number
        self.contrasena = contrasena
        self.created_at = created_at

    def __repr__(self):
        return '<Teacher %r>' % self.firstname

    def serialize(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "phone_number": self.phone_number,
            "contrasena": self.contrasena,
        }


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    firstname = db.Column(db.String(30), nullable=False,
                          unique=False, default=False)
    lastname = db.Column(db.String(60), nullable=False,
                         unique=True, default=False)
    dni = db.Column(db.String(20), nullable=False, unique=True, default=False)
    email = db.Column(db.String(99), nullable=False,
                      unique=True, default=False)
    contrasena = db.Column(db.String(255), nullable=False,
                           unique=True, default=False)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False)
    modified_at = db.Column(db.DateTime(timezone=True), nullable=True)


def __init__(self, firstname, lastname, email, contrasena, code_teacher, created_at):
    self.firstname = firstname
    self.lastname = lastname
    self.dni = dni
    self.email = email
    self.contrasena = contrasena
    self.created_at = created_at


def __repr__(self):
    return '<Student %r>' % self.firstname


def serialize(self):
    return {
        "id": self.id
        "firstname": self.firstname
        "lastname": self.lastname
        "dni": self.dni
        "email": self.email
        "contrasena": self.contrasena
    }
