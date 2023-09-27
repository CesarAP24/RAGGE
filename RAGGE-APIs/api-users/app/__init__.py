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

    @app.route('/teachers', methods=['POST'])
    def create_teacher():
        returned_code = 201
        list_errors = []

        try:
            body = request.json

            required_fields = ['name', 'email', 'dni', 'code', 'phone_number']

            for field in required_fields:
                if field not in body:
                    list_errors.append(field + ' is required')

            if 'dni' in body and len(body['dni']) != 8:
                list_errors.append('dni must have 8 digits')

            if len(list_errors) > 0:
                returned_code = 400
            else:
                #crear usuario
                new_user = User(
                    id=str(uuid.uuid4()),
                    name=body['name'],
                    dni=body['dni'],
                    email=body['email'],
                    contrasena="R4gg3" + body['dni'][0:4],
                    created_at=datetime.utcnow()
                )

                db.session.add(new_user)
                db.session.commit()

                #crear profesor
                new_teacher = Teacher(
                    id=new_user.id,
                    phone_number=body['phone_number']
                )

                db.session.add(new_teacher)
                db.session.commit()

                teacher_id = new_teacher.id
        
        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error registering teacher', 'errors': list_errors}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'id': teacher_id, 'success': True, 'message': 'Teacher registered successfully'}), returned_code

    @app.route('/teachers/<teacher_id>', methods=['PATCH'])
    def update_teacher(teacher_id):
        code = 200
        
        #check cookies
        if session.get('user_id') is None:
            abort(401)
        
        if Teacher.query.filter_by(id=session.get('user_id')).first() is None:
            abort(403)

        try:
            teacher = Teacher.query.get(teacher_id)
            user = User.query.get(teacher_id)


            if teacher is None:
                code = 404
                message = 'Teacher not found'
            
            if user is None:
                code = 404
                message = 'User not found'


            data = request.json

            if 'phone_number' in data:
                teacher.phone_number = data['phone_number']
            if 'name' in data:
                user.name = data['name']
            if 'dni' in data:
                if len(data['dni']) != 8:
                    code = 400
                    message = 'dni must have 8 digits'
                else:
                    user.dni = data['dni']
            if 'email' in data:
                user.email = data['email']
            if 'contrasena' in data:
                user.contrasena = data['contrasena']

            db.session.commit()

        except Exception as e:
            db.session.rollback()
            code = 500

        if code == 404:
            return jsonify({'success': False, 'message': message}), code
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Teacher updated successfully'}), code
        
    @app.route('/teachers/<teacher_id>', methods=['DELETE'])
    def delete_teacher(teacher_id):
        code = 204
        
        #check cookie
        if session.get('user_id') is None:
            abort(401)

        teacher = Teacher.query.filter_by(id=session.get('user_id')).first()

        if teacher is None or teacher_id != session.get('user_id'):
            abort(403)

        try:

            #confirmation with name
            data = request.json

            if 'confirmation' not in data:
                return jsonify({'success': False, 'message': 'Confirmation is required (should be the name of the teacher)'}), 400

            if data['confirmation'] != teacher.name:
                return jsonify({'success': False, 'message': 'Confirmation failed (should be the name of the teacher)'}), 400


            teacher = Teacher.query.get(teacher_id)
            user = User.query.get(teacher_id)

            #eliminar notas calificadas por el profesor
            scores = Score.query.filter_by(id_teacher=teacher_id).all()
            for score in scores:
                db.session.delete(score)
            
            db.session.commit()

            #eliminar tareas del profesor
            homeworks = Homework.query.filter_by(id_teacher=teacher_id).all()
            for homework in homeworks:
                db.session.delete(homework)
            
            db.session.commit()

            #eliminar cursos del profesor
            courses = Course.query.filter_by(id_teacher=teacher_id).all()
            for course in courses:
                # eliminar relaciones ATieneC
                atienec = ATieneC.query.filter_by(id_curso=course.id_course).all()
                for atc in atienec:
                    db.session.delete(atc)
                db.session.commit()

                db.session.delete(course)
            
            db.session.commit()

            #eliminar profesor
            db.session.delete(teacher)
            db.session.commit()

            #eliminar usuario
            db.session.delete(user)
            db.session.commit()

        except Exception as e:
            db.session.rollback()
            code = 500

    @app.route('/teachers/<teacher_id>', methods=['GET'])
    def get_teacher(teacher_id):
        code = 200

        #check cookie
        if session.get('user_id') is None:
            abort(401)
        teacher = Teacher.query.filter_by(id=session.get('user_id')).first()
        if teacher is None or teacher_id != session.get('user_id'):
            abort(403)

        try:
            user = User.query.get(teacher_id)
            if user is None or teacher is None:
                code = 404
                message = "Teacher not found"
            else:
                teacher_data = teacher.serialize()
                user_data = user.serialize()
                teacher_data.update(user_data)
                #quitar la contrasena
                teacher_data.pop('contrasena', None)
        except Exception as e:
            code = 500
            db.session.rollback()
        
        if code == 404:
            return jsonify({'success': False, 'message': message}), code
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'teacher': teacher_data}), code
        
    @app.route('/students', methods=['POST'])
    def create_student():
        returned_code = 201
        list_errors = []

        #check cookie
        if session.get('user_id') is None:
            abort(401)

        if Teacher.query.filter_by(id=session.get('user_id')).first() is None:
            abort(403)

        try:
            body = request.json

            required_fields = ['name', 'email', 'dni']

            for field in required_fields:
                if field not in body:
                    list_errors.append(field + ' is required')

            if len(list_errors) > 0:
                returned_code = 400
            else:
                new_user = User(
                    id=str(uuid.uuid4()),
                    name=body['name'],
                    dni=body['dni'],
                    email=body['email'],
                    contrasena="R4gg3" + body['dni'][0:4],
                    created_at=datetime.utcnow()
                )

                db.session.add(new_user)

                new_student = Student(
                    id=new_user.id
                )

                db.session.add(new_student)

                db.session.commit()

        except Exception as e:
            db.session.rollback()
            returned_code = 500

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error registering student', 'errors': list_errors}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'message': 'Student registered successfully', 'id': new_student.id}), returned_code

    @app.route('/students/<student_id>', methods=['DELETE'])
    def delete_student(student_id):
        #check cookie
        if session.get('user_id') is None:
            abort(401)
            
        if Teacher.query.filter_by(id=session.get('user_id')).first() is None:
            abort(403)

        try:
            student = Student.query.filter_by(id=student_id).first()

            if student is None:
                return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404

            db.session.delete(student)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Estudiante eliminado exitosamente'}), 204

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error al eliminar el estudiante'}), 500

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
