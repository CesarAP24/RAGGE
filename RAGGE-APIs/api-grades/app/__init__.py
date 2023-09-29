
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
        CORS(app, origins='*', supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # ROUTES API -----------------------------------------------------------
    @app.route('/courses/<course_id>/homeworks/<homework_id>', methods=['GET'])
    def get_specific_homework(course_id, homework_id):
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if User.query.filter_by(id=cookie).first() is None:
            abort(403)
        try:
            course = Course.query.get(course_id)

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homework = Homework.query.filter_by(id=homework_id, id_course=course_id).first()
            print(homework)

            if not(homework):
                return jsonify({'success': False, 'message': 'Tarea no encontrada en este curso'}), 404

            homework_data = homework.serialize()

            return jsonify({'success': True, 'homework': homework_data}), 200

        except Exception as e:
            print(sys.exc_info())
            return jsonify({'success': False, 'message': 'Error al obtener la tarea (homework)'}), 500


    @app.route('/courses/<course_id>/homeworks', methods=['POST'])
    def create_homework(course_id):
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)

        code = 201
        list_errors = []

        try:
            curso = Course.query.get(course_id)
            if curso is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404
        
            data = request.json

            fields = ['name', 'deadline', 'indications']

            if 'name' not in data:
                list_errors.append('name is required')
            elif len(data['name']) > 200:
                list_errors.append('name must be less than 200 characters')
            
            if 'deadline' not in data:
                list_errors.append('deadline is required with this format: YYYY-MM-DD HH:MM:SS')
            else:
                try:
                    datetime.strptime(data['deadline'], '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    list_errors.append('deadline must have this format: YYYY-MM-DD HH:MM:SS')
            
            if 'indications' not in data:
                list_errors.append('indications is required')
            elif len(data['indications']) > 1000:
                list_errors.append('indications must be less than 1000 characters')
            

            if len(list_errors) > 0:
                code = 400
            else:
                new_homework = Homework(
                    id_course=course_id,
                    name=data['name'],
                    deadline=data['deadline'],
                    indications=data['indications'],
                    id_teacher=cookie,
                    created_at=datetime.utcnow()
                )

                db.session.add(new_homework)
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            code = 500
            print(sys.exc_info())
        
        if code == 400:
            return jsonify({'success': False, 'message': 'Error al crear la tarea', 'errors': list_errors}), code
        elif code != 201:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Tarea creada exitosamente'}), code


    @app.route('/courses/<course_id>/homeworks', methods=['GET'])
    def get_course_homeworks(course_id):
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if User.query.filter_by(id=cookie).first() is None:
            abort(403)
        try:
            course = Course.query.get(course_id)

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homeworks = Homework.query.filter_by(id_course=course_id).all()

            homework_data = [homework.serialize() for homework in homeworks]

            if len(homework_data) == 0:
                return jsonify({'success': False, 'message': 'No hay tareas en este curso', 'homeworks': homework_data}), 200

            return jsonify({'success': True, 'homeworks': homework_data}), 200

        except Exception as e:
            print(sys.exc_info())
            return jsonify({'success': False, 'message': 'Error al obtener tareas del curso'}), 500


    @app.route('/courses/<course_id>/homeworks/<homework_id>/scores', methods=['GET'])
    def get_homework_students(course_id, homework_id):
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)

        code = 200
        try:
            #check course exists
            if Course.query.get(course_id) is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404
            #check homework exists
            if Homework.query.filter_by(id=homework_id, id_course=course_id).first() is None:
                return jsonify({'success': False, 'message': 'Tarea no encontrada en este curso'}), 404
            
            scores = Score.query.filter_by(id_homework=homework_id, id_course=course_id).all()

            scores = [score.serialize() for score in scores]

            #añadir datos del estudiante
            for score in scores:
                student = User.query.get(score['id_student'])
                score['student_name'] = student.name
                

            return jsonify({'success': True, 'scores': scores}), code
        except Exception as e:
            print(sys.exc_info())
            code = 500
            return jsonify({'success': False, 'message': 'Error al obtener las notas'}), code


    @app.route('/courses/<course_id>/homeworks/<homework_id>/scores', methods=['POST'])
    def create_score(course_id, homework_id):
        code = 201
        list_errors = []

        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)
        
        try:
            course = Course.query.get(course_id)

            try:
                data = request.json
            except:
                return jsonify({'success': False, 'message': 'Error al obtener JSON'}), 400
        

            if 'id_student' not in data:
                return jsonify({'success': False, 'message': 'id_student is required'}), 400

            if course is None:
                return jsonify({'success': False, 'message': 'Curso no encontrado'}), 404

            homework = Homework.query.filter_by(id=homework_id, id_course=course_id).first()

            if not(homework):
                return jsonify({'success': False, 'message': 'Tarea no encontrada en este curso'}), 404

            student = Student.query.get(data['id_student'])

            if student is None:
                return jsonify({'success': False, 'message': 'Estudiante no encontrado'}), 404

            data = request.json

            if 'value' not in data:
                list_errors.append('value is required')
            elif float(data['value']) < 0 or float(data['value']) > 20:
                list_errors.append('value must be between 0 and 20')
            

            if len(list_errors) > 0:
                code = 400
            else:
                new_score = Score(
                    date = datetime.utcnow(),
                    id_homework=homework_id,
                    id_course=course_id,
                    value=data['value'],
                    id_student=data['id_student'],
                    id_teacher=cookie,
                    created_at=datetime.utcnow()
                )

                db.session.add(new_score)
                db.session.commit()

        except Exception as e:
            db.session.rollback()
            code = 500
            print(sys.exc_info())

        if code == 400:
            return jsonify({'success': False, 'message': 'Error al crear la nota', 'errors': list_errors}), code
        elif code != 201:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Nota creada exitosamente'}), code

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
