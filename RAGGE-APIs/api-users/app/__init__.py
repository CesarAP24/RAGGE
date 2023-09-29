# Libraries

from .models import *
from flask_cors import CORS
from .utilities import *
import requests

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


class BearerAuth(requests.auth.AuthBase):
    def __init__(self, token):
        self.token = token
    def __call__(self, r):
        r.headers["authorization"] = "Bearer " + self.token
        return r

# App
def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = 'pneumonoultramicroscopicsilicovolcanoconiosis'

    with app.app_context():
        setup_db(app, test_config['database_path'] if test_config else None)
        CORS(app, origins="*", supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # ROUTES API -----------------------------------------------------------

    @app.route('/teachers/<teacher_id>', methods=['PATCH'])
    def update_teacher(teacher_id):
        code = 200

        # check cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
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
        code = 200

        # check cookie
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        teacher = Teacher.query.filter_by(id=cookie).first()
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)

        try:

            # confirmation with name
            data = request.json

            teacher = User.query.get(teacher_id)

            if teacher is None:
                return jsonify({'success': False, 'message': 'Teacher not found'}), 404

            if 'confirmation' not in data:
                return jsonify({'success': False, 'message': 'Confirmation is required (should be the name of the teacher)'}), 400

            if data['confirmation'] != teacher.name:
                return jsonify({'success': False, 'message': 'Confirmation failed (should be the name of the teacher)'}), 400

            teacher = Teacher.query.get(teacher_id)
            user = User.query.get(teacher_id)

            # eliminar notas calificadas por el profesor
            scores = Score.query.filter_by(id_teacher=teacher_id).all()
            for score in scores:
                db.session.delete(score)

            db.session.commit()

            # eliminar tareas del profesor
            homeworks = Homework.query.filter_by(id_teacher=teacher_id).all()
            for homework in homeworks:
                db.session.delete(homework)

            db.session.commit()

            # eliminar cursos del profesor
            courses = Course.query.filter_by(id_teacher=teacher_id).all()
            for course in courses:
                # eliminar relaciones ATieneC
                atienec = ATieneC.query.filter_by(
                    id_curso=course.id_course).all()
                for atc in atienec:
                    db.session.delete(atc)
                db.session.commit()

                db.session.delete(course)

            db.session.commit()

            # eliminar profesor
            db.session.delete(teacher)
            db.session.commit()

            # eliminar usuario
            db.session.delete(user)
            db.session.commit()

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            code = 500

        if code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Teacher deleted successfully'}), code

    @app.route('/teachers', methods=['GET'])
    def get_teachers():
        code = 200

        # check cookie
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if User.query.filter_by(id=cookie).first() is None:
            abort(403)

        try:
            teachers = Teacher.query.all()
            teachers = [teacher.serialize() for teacher in teachers]
            teachers = [User.query.filter_by(
                id=teacher['id']).first() for teacher in teachers]
            teachers = [teacher.serialize() for teacher in teachers]
            # quitar la contrasena
            for teacher in teachers:
                teacher.pop('contrasena', None)
        except Exception as e:
            code = 500
            db.session.rollback()

        if code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'teachers': teachers}), code
        

    @app.route('/teachers/<teacher_id>', methods=['GET'])
    def get_teacher(teacher_id):
        code = 200

        # check cookie
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        teacher = Teacher.query.filter_by(id=cookie).first()
        if teacher is None or teacher_id != cookie:
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
                # quitar la contrasena
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

        # check cookie
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
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
                #checkear que no exista
                if User.query.filter_by(dni=body['dni']).first() is not None:
                    returned_code = 400
                    list_errors.append('El DNI ya está registrado')
                elif User.query.filter_by(email=body['email']).first() is not None:
                    returned_code = 400
                    list_errors.append('El correo ya está registrado')
                else:
                    # crear usuario
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

                    new_student = Student(
                        id=new_user.id
                    )

                    db.session.add(new_student)

                    db.session.commit()

        except Exception as e:
            print(sys.exc_info())
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
        # check cookie
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)

        try:
            student = Student.query.filter_by(id=student_id).first()

            if student is None:
                return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404
            

            #eliminar relaciones ATieneC
            atienec = ATieneC.query.filter_by(id_alumno=student_id).all()
            for atc in atienec:
                db.session.delete(atc)
            db.session.commit()

            #eliminar notas calificadas por el profesor
            scores = Score.query.filter_by(id_student=student_id).all()
            for score in scores:
                db.session.delete(score)
            db.session.commit()

            #eliminar estudiante
            db.session.delete(student)
            db.session.commit()

            #eliminar usuario
            user = User.query.filter_by(id=student_id).first()
            db.session.delete(user)
            db.session.commit()


            return jsonify({'success': True, 'message': 'Estudiante eliminado exitosamente'}), 200

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

            if 'dni' not in body or body['dni'] == '':
                list_error.append('DNI es requerido')
            elif len(body['dni']) != 8:
                list_error.append('DNI debe tener 8 dígitos')
            else:
                dni = body['dni']

            if 'name' not in body or body['name'] == '':
                list_error.append('Nombre es requerido')
            else:
                name = body['name']

            if 'email' not in body or body['email'] == '':
                list_error.append('Correo es requerido')
            elif '@' not in body['email'] or '.' not in body['email']:
                list_error.append('Correo inválido')
            else:
                email = body['email']

            if 'code' not in body or body['code'] == '':
                list_error.append('Es requerido un código de verificación')
            else:
                code = body['code']

            if 'phone_number' not in body:
                list_error.append('Es requerido un número de teléfono ("phone_number")')
            elif len(str(body['phone_number'])) != 9:
                list_error.append('Número de teléfono inválido')
            else:
                phone_number = body['phone_number']

            if len(list_error) > 0:
                returned_code = 400
            else:
                # verificar campo codigo de verificacion lleno
                codigo = Code.query.filter_by(code=code).first()
                if codigo is None:
                    returned_code = 400
                    list_error.append('Código de verificación incorrecto')
                else:
                    # verificar si el codigo ya fue usado
                    if User.query.filter_by(dni=dni).first():
                        returned_code = 400
                        list_error.append('El DNI ya está registrado')
                    if User.query.filter_by(email=email).first():
                        returned_code = 400
                        list_error.append('El correo ya está registrado')
                    if Teacher.query.filter_by(phone_number=phone_number).first():
                        returned_code = 400
                        list_error.append('El número de teléfono ya está registrado')
                    
                    if returned_code == 201:
                        if codigo.used:
                            returned_code = 400
                            list_error.append('Código de verificación incorrecto')
                        else:
                            # generar contraseña
                            contrasena = "R4gg3" + dni[0:4]

                            # crear usuario
                            user = User(name=name, dni=dni, email=email,
                                        contrasena=contrasena, created_at=datetime.utcnow())
                            db.session.add(user)
                            db.session.commit()


                            teacher = Teacher(id=user.id, phone_number=phone_number)
                            db.session.add(teacher)
                            db.session.commit()

                            # marcar codigo como usado
                            codigo.used = True
                            db.session.commit()

                            # guardar en session el id del usuario
                            cookie = user.id

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error en el registro', 'errors': list_error}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'message': 'Usuario registrado correctamente', 'contrasena': contrasena, 'cookie': cookie}), returned_code

    @app.route('/login', methods=['POST'])
    def login():
        # authorization
        return_code = 200
        list_error = []

        try:
            body = request.json
            if 'dni' not in body or body['dni'] == '':
                list_error.append('DNI es requerido para iniciar sesión')
            else:
                dni = body['dni']

            if 'contrasena' not in body or body['contrasena'] == '':
                list_error.append(
                    'Contraseña es requerida para iniciar sesión')
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
                        cookie = user.id

        except Exception as e:
            print(sys.exc_info())
            return_code = 500

        if return_code == 400:
            return jsonify({'success': False, 'message': 'Error en la autenticación', 'errors': list_error}), return_code
        elif return_code == 404:
            return jsonify({'success': False, 'message': 'Usuario no encontrado', 'errors': list_error}), return_code
        elif return_code != 200:
            abort(return_code)
        else:
            return jsonify({'success': True, 'message': 'Usuario autenticado correctamente', "cookie": cookie}), return_code

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
            alumnos = [User.query.filter_by(
                id=alumno['id']).first() for alumno in alumnos]

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
                    alumnos_curso = ATieneC.query.filter_by(
                        id_curso=course.id_course).all()
                    alumnos_curso = [
                        alumno_curso.id_alumno for alumno_curso in alumnos_curso]
                    # alumnos q tienen id presente en alumnos_curso
                    alumnos = [
                        alumno for alumno in alumnos if alumno.id in alumnos_curso]

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


    @app.route('/codes', methods=['POST'])
    def send_code():
        try:
            try:
                data = request.json
                email = data['email']
            except:
                return jsonify({'success': False, 'message': 'Debe enviar un JSON con "email'}), 500
        
        
            code = str(generate_random_code())
            prev_code = Code.query.filter_by(code=code).first()

            if prev_code:
                prev_code.used = False
            else:
                new_code = Code(code=code, used=False)
                db.session.add(new_code)
            
            db.session.commit()

            # enviar correo

            BASE_URL = "https://api.sendgrid.com/v3/mail/send"
            json = {
                "personalizations": [
                    {
                        "to": 
                        [{
                            "email": email
                        }],
                        "dynamic_template_data":
                        {
                            "code": code
                        }
                    }
                ],
                "from": {
                    "email": "cesar.perales@utec.edu.pe"
                },
                "template_id": "d-575691d815d64971b3ec02377ef9e712",
            }

            headers = { #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
                "Content-Type": "application/json"
            }

            response = requests.post(BASE_URL, json=json, headers=headers, auth=BearerAuth('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'))
            print(response.status_code)

            if response.status_code != 202:
                return jsonify({'success': False, 'message': 'Erro al enviar, intente más tarde'}), 500

            return jsonify({'success': True, 'message': 'Código enviado exitosamente'}), 201

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error al enviar el código'}), 500

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
