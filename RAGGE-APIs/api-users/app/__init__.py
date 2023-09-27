# Libraries

from .models import *
from flask_cors import CORS
from .utilities import *

from flask import (
    Flask,
    render_template,
    jsonify,
    request,
    redirect,
    abort,
    session,
)

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
from flask import make_response


import sys
import uuid
import json
import os
from datetime import datetime
from datetime import timedelta


# App
def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = 'pneumonoultramicroscopicsilicovolcanoconiosis'

    with app.app_context():
        setup_db(app, test_config['database_path'] if test_config else None)
        CORS(app, origins=['http://localhost:8081'], supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # ROUTES API -----------------------------------------------------------
    @app.route('/register', methods=['POST'])
    def register():
        returned_code = 201
        list_error = []
        try:
            body = request.json

            if 'dni' not in body:
                list_error.append('DNI es requerido')
            else:
                dni = body['dni']

            if 'name' not in body:
                list_error.append('Nombre es requerido')
            else:
                name = body['name']

            if 'email' not in body:
                list_error.append('Correo es requerido')
            else:
                email = body['email']

            if 'code' not in body:
                list_error.append('Es requerido un código de verificación')
            else:
                code = body['code']

            if len(list_error) > 0:
                returned_code = 400
            else:
                # verificar codigo de verificacion
                codigo = Code.query.filter_by(code=code).first()
                if codigo is None:
                    returned_code = 400
                    list_error.append('Código de verificación incorrecto')
                else:
                    # verificar si el codigo ya fue usado
                    if codigo.used:
                        returned_code = 400
                        list_error.append('Código de verificación incorrecto')
                    else:
                        # generar contraseña
                        contrasena = generate_password()

                        # crear usuario
                        user = User(name=name, dni=dni, email=email, contrasena=contrasena)
                        db.session.add(user)
                        db.session.commit()

                        # marcar codigo como usado
                        codigo.used = True
                        db.session.commit()

                        # guardar en session el id del usuario
                        session['user_id'] = user.id

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error en el registro', 'errors': list_error}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'message': 'Usuario registrado correctamente', 'contrasena': contrasena}), returned_code

    @app.route('/login', methods=['POST'])
    def login():
        return_code = 200
        list_error = []

        try:
            body = request.json
            if 'dni' not in body:
                list_error.append('DNI es requerido para iniciar sesión')
            else:
                dni = body['dni']

            if 'contrasena' not in body:
                list_error.append('Contraseña es requerida para iniciar sesión')
            else:
                contrasena = body['contrasena']


            if len(list_error) > 0:
                return_code = 400
            else:
                user = User.query.filter_by(dni=dni).first()

                if user is None:
                    # si no existe el usuario
                    return_code = 404
                    list_error.append('Usuario no encontrado')
                else:
                    # si existe el usuario
                    if user.contrasena != contrasena:
                        # si la contraseña no coincide
                        return_code = 400
                        list_error.append('Contraseña incorrecta')
                    else:
                        # si la contraseña coincide guardar en session el id del usuario
                        session['user_id'] = user.id

        except Exception as e:
            print(sys.exc_info())
            returned_code = 500


        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error en la autenticación', 'errors': list_error}), returned_code
        elif return_code == 404:
            return jsonify({'success': False, 'message': 'Usuario no encontrado', 'errors': list_error}), return_code
        elif returned_code != 200:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'message': 'Usuario autenticado correctamente'}), returned_code

    @app.route('/students', methods=['GET'])
    def get_students():
        returned_code = 200
        error_message = ''
        students_list = []

        try:
            nombre = request.args.get('nombre', None)
            curso = request.args.get('curso', None)
            dni = request.args.get('dni', None)

            alumnos = Student.query.all()
            alumnos = [alumno.serialize() for alumno in alumnos]
            alumnos = [User.query.filter_by(id=alumno['id']).first() for alumno in alumnos]

            if nombre:
                for alumno in alumnos:
                    # si el nombre esta en el nombre
                    if nombre.lower() in alumno.name.lower():
                        students_list.append(alumno.serialize())
                alumnos = students_list
                students_list = []

            if curso:
                course = Course.query.filter_by(name=curso).first()
                if course:
                    alumnos_curso = ATieneC.query.filter_by(id_curso=course.id_course).all()
                    alumnos_curso = [alumno_curso.id_alumno for alumno_curso in alumnos_curso]
                    #alumnos q tienen id presente en alumnos_curso
                    alumnos = [alumno for alumno in alumnos if alumno.id in alumnos_curso]
            
            if dni:
                alumnos = [alumno for alumno in alumnos if dni in alumno.dni]

            
            students_list = [alumno.serialize() for alumno in alumnos]
            
            if len(students_list) == 0:
                returned_code = 404
                error_message = 'No students found'

        except Exception as e:
            print(sys.exc_info())
            returned_code = 500

        if returned_code == 404:
            return jsonify({'success': False, 'message': error_message}), returned_code
        elif returned_code != 200:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'students': students_list}), returned_code

    # HANDLE ERROR ---------------------------------------------------------
    
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"success": False, "message": 'Resource not found'}), 404

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"success": False, "message": 'Unauthorized'}), 401

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "message": 'Bad request'}), 400

    @app.errorhandler(405)
    def not_allowed(error):
        return jsonify({"success": False, "message": 'Method not allowed'}), 405

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"success": False, "message": 'Forbidden'}), 403

    @app.errorhandler(409)
    def conflict(error):
        return jsonify({"success": False, "message": 'Conflict'}), 409

    @app.errorhandler(500)
    def server_error(error):
        return jsonify({"success": False, "message": 'Server error'}), 500

    @app.errorhandler(501)
    def not_implemented(error):
        return jsonify({"success": False, "message": 'Not implemented'}), 501

    return app
