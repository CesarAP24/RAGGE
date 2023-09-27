
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
from .models import db, setup_db, User, Teacher, Student, Homework, Score, Course, ATieneC
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
        


    # @app.route('/students', methods=['POST'])
    # def create_student():
    #     returned_code = 201
    #     list_errors = []

    #     try:
    #         body = request.json

    #         required_fields = ['firstname', 'lastname', 'email', 'contrasena']

    #         for field in required_fields:
    #             if field not in body:
    #                 list_errors.append(field)

    #         if len(list_errors) > 0:
    #             returned_code = 400
    #         else:
    #             new_student(
    #                 id=str(uuid.uuid4()),
    #                 firstname=body['firstname'],
    #                 lastname=body['lastname'],
    #                 email=body['email'],
    #                 contrasena=body['contrasena']
    #             )

    #             db.session.add(new_student)
    #             db.session.commit()
    #             student_id = new_student.id

    #     except Exception as e:
    #         db.session.rollback()
    #         returned_code = 500

    #     finally:
    #         db.session.close()

    #     if returned_code == 400:
    #         return jsonify({'success': False, 'message': 'Error registering student', 'errirs': list_errros}), returned_code
    #     elif returned_code != 201:
    #         abort(returned_code)
    #     else:
    #         return jsonify({'id': student_id, 'success': True, 'message': 'Student registered successfully'}), returned_code

    # @app.route('/students/<string:student_id>', methods=['DELETE'])
    # def delete_student(student_id):
    #     #check cookie
    #     if session.get('user_id') is None:
    #         abort(401)
            
    #     if Teacher.query.filter_by(id=session.get('user_id')).first() is None:
    #         abort(403)

    #     try:
    #         student = Student.query.filter_by(id=student_id).first()

    #         if student is None:
    #             return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404

    #         db.session.delete(student)
    #         b.session.commit()

    #         return jsonify({'success': True, 'message': 'Estudiante eliminado exitosamente'}), 204

    #     except Exception as e:
    #         db.session.rollback()
    #         return jsonify({'success': False, 'message': 'Error al eliminar el estudiante'}), 500

    #     finally:
    #         db.session.close()

    # @app.route('/courses/<string:course_id>/homeworks/<string:homework_id>', methods=['GET'])
    # def get_specific_homework(course_id, homework_id):
    #     try:
    #         course = Course.query.get(course_id)

    #         if course is None:
    #             return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

    #         homework = Homework.query.get(homework_id)

    #         if homework is None or homework.id_course != course_id:
    #             return jsonify({'success': False, 'message': 'Tarea (homework) no encontrada en este curso'}), 404

    #         homework_data = homework.serialize()

    #         return jsonify({'success': True, 'homework': homework_data}), 200

    #     except Exception as e:
    #         return jsonify({'success': False, 'message': 'Error al obtener la tarea (homework)'}), 500

    # @app.route('/courses/<string:course_id>/homeworks', methods=['GET'])
    # def get_course_homeworks(course_id):
    #     try:
    #         course = Course.query.get(course_id)

    #         if course is None:
    #             return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

    #         homeworks = Homework.query.filter_by(id_course=course_id).all()

    #         homework_data = [homework.serialize() for homework in homeworks]

    #         if len(homework_data) == 0:
    #             return jsonify({'success': False, 'message': 'No hay tareas (homeworks) en este curso', 'homeworks': homework_data}), 200

    #         return jsonify({'success': True, 'homeworks': homework_data}), 200

    #     except Exception as e:
    #         return jsonify({'success': False, 'message': 'Error al obtener tareas del curso'}), 500

    # @app.route('/courses/<string:course_id>/homeworks/<string:homework_id>/students/<string:student_id>/scores', methods=['POST'])
    # def create_score(course_id, homework_id, student_id):
    #     try:
    #         if not current_user.is_authenticated:
    #             return jsonify({'success': False, 'message': 'Usuario no autenticado'}), 401

    #         course = Course.query.get(course_id)

    #         if course is None:
    #             return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

    #         homework = Homework.query.get(homework_id)

    #         if homework is None:
    #             return jsonify({'success': False, 'message': 'Tarea (homework) no encontrada'}), 404

    #         student = Student.query.get(student_id)

    #         if student is None:
    #             return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404

    #         teacher = Teacher.query.filter_by(
    #             course_id=course_id, user_id=current_user.id).first()

    #         if teacher is None:
    #             return jsonify({'success': False, 'message': 'No tienes permiso para calificar a este estudiante en este curso'}), 403

    #         new_score = Score(
    #             date=datetime.utcnow(),
    #             value=0,
    #         )

    #         db.session.add(new_score)
    #         db.session.commit()

    #         return jsonify({'success': True, 'message': 'Nota creada exitosamente'}), 201

    #     except Exception as e:
    #         return jsonify({'success': False, 'message': 'Error al crear la nota'}), 500

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
