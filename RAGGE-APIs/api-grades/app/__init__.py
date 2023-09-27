
from flask import (
    session,
    Flask,
    jsonify,
    request,
    abort
)
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey
import sys
import uuid
import json
import os
from datetime import datetime
from datetime import timedelta
from .models import db, setup_db, User, Teacher, Student, Homework, Score, Course
from flask_cors import CORS


def create_app(config=None):
    app = Flask(__name__)
    with app.app_context():
        setup_db(app, config['database_path'] if config else None)
        CORS(app, origins='http://localhost:8080')

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

            if 'firstname' not in body:
                list_errors.append('firstname')
            else:
                firstname = body['firstname']

            if 'lastname' not in body:
            else:
                lastname = body['lastname']

            if 'email' not in body:
                list_errors.append('email')
            else:
                email = body['email']

            if 'contrasena' not in body:
                list_errors.append('contrasena')
            else:
                contrasena = body['contrasena']

            if len(list_errors) > 0:
                returned_code = 400
            else:
                new_teacher = Teacher(
                    id=str(uuid.uuid4()),
                    firstname=firstname,
                    lastname=lastname,
                    dni=body['dni'],
                    phone_number=body['phone_number'],
                    email=email,
                    contrasena=contrasena
                )

                db.session.add(new_teacher)
                db.session.commit()
                client_id = new_teacher.id

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500

        finally:
            db.session.close()

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error registering teacher', 'errors': list_errors}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'id': client_id, 'success': True, 'message': 'Teacher registered successfully!'}), returned_code

    @app.route('/teachers/<string>:teacher_id', methods=['PATCH'])
    def update_teacher(teacher_id):
        try:
            teacher = Teacher.query.get(teacher_id)

            if teacher is None:
                return jsonify({'success': False, 'message': 'Teacher not found'}), 404

            data = request.json

            if 'phone_number' in data:
                teacher.phone_number = data['phone_number']
            if 'firstname' in data:
                teacher.firstname = data['firstname']
            if 'lastname' in data:
                teacher.lastname = data['lastname']
            if 'dni' in data:
                teacher.dni = data['dni']
            if 'email' in data:
                teacher.email = data['email']
            if 'contrasena' in data:
                teacher.contrasena = data['contrasena']

            db.session.commit()

            return jsonify({'success': True, 'message': 'Profesor actualizado exitosamente'}), 200

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error al actualizar el profesor'}), 500

        finally:
            db.session.close()

    @app.route('/teacher', methods=['DELETE'])
    def delete_teacher(teacher_id):
        try:
            teacher = Teacher.query.get(teacher_id)

            if teacher is None:
                return jsonify({'success': False, 'message': 'Profesor no encontrado'}), 404

            db.session.delete(teacher)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Profesor eliminado exitosamente'}), 204

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error al eliminar el profesor'}), 500

        finally:
            db.session.close()

    @app.route('/teachers/<string:teacher_id>', methods=['GET'])
    def get_teacher(teacher_id):
        try:
            teacher = Teacher.query.get(teacher_id)

            if teacher is None:
                return jsonify({'success': False, 'message': 'Profesor no encontrado'}), 404

            teacher_data = {
                'id': teacher.id,
                'firstname': teacher.firstname,
                'lastname': teacher.lastname,
                'dni': teacher.dni,
                'email': teacher.email,
                'phone_number': teacher.phone_number
            }

            return jsonify({'success': True, 'teacher': teacher_data}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error al obtener información del profesor'}), 500

    @app.route('/students', methods=['POST'])
    def create_student():
        returned_code = 201
        list_errors = []

        try:
            body = request.json

            required_fields = ['firstname', 'lastname', 'email', 'contrasena']

            for field in required_fields:
                if field not in body:
                    list_errors.append(field)

            if len(list_errors) > 0:
                returned_code = 400
            else:
                new_student(
                    id=str(uuid.uuid4()),
                    firstname=body['firstname'],
                    lastname=body['lastname'],
                    email=body['email'],
                    contrasena=body['contrasena']
                )

                db.session.add(new_student)
                db.session.commit()
                student_id = new_student.id

        except Exception as e:
            db.session.rollback()
            returned_code = 500

        finally:
            db.session.close()

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error registering student', 'errirs': list_errros}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'id': student_id, 'success': True, 'message': 'Student registered successfully'}), returned_code

    @app.route('/students/<string:student_id>', methods=['DELETE'])
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
            b.session.commit()

            return jsonify({'success': True, 'message': 'Estudiante eliminado exitosamente'}), 204

        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': 'Error al eliminar el estudiante'}), 500

        finally:
            db.session.close()

    @app.route('/courses/<string:course_id>/homeworks/<string:homework_id>', methods=['GET'])
    def get_specific_homework(course_id, homework_id):
        try:
            course = Course.query.get(course_id)

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homework = Homework.query.get(homework_id)

            if homework is None or homework.id_course != course_id:
                return jsonify({'success': False, 'message': 'Tarea (homework) no encontrada en este curso'}), 404

            homework_data = homework.serialize()

            return jsonify({'success': True, 'homework': homework_data}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error al obtener la tarea (homework)'}), 500

    @app.route('/courses/<string:course_id>/homeworks', methods=['GET'])
    def get_course_homeworks(course_id):
        try:
            course = Course.query.get(course_id)

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homeworks = Homework.query.filter_by(id_course=course_id).all()

            homework_data = [homework.serialize() for homework in homeworks]

            if len(homework_data) == 0:
                return jsonify({'success': False, 'message': 'No hay tareas (homeworks) en este curso', 'homeworks': homework_data}), 200

            return jsonify({'success': True, 'homeworks': homework_data}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error al obtener tareas del curso'}), 500

    @app.route('/courses/<string:course_id>/homeworks/<string:homework_id>/students/<string:student_id>/scores', methods=['POST'])
    def create_score(course_id, homework_id, student_id):
        try:
            if not current_user.is_authenticated:
                return jsonify({'success': False, 'message': 'Usuario no autenticado'}), 401

            course = Course.query.get(course_id)

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homework = Homework.query.get(homework_id)

            if homework is None:
                return jsonify({'success': False, 'message': 'Tarea (homework) no encontrada'}), 404

            student = Student.query.get(student_id)

            if student is None:
                return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404

            teacher = Teacher.query.filter_by(
                course_id=course_id, user_id=current_user.id).first()

            if teacher is None:
                return jsonify({'success': False, 'message': 'No tienes permiso para calificar a este estudiante en este curso'}), 403

            new_score = Score(
                date=datetime.utcnow(),
                value=0,
            )

            db.session.add(new_score)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Nota creada exitosamente'}), 201

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error al crear la nota'}), 500

    #  HANDLE ERROR ---------------------------------------------------------

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
