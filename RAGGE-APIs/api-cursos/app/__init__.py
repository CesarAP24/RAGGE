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
    app.config['JWT_SECRET_KEY'] = 'pneumonoultramicroscopicsilicovolcanoconiosis'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']

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
    @app.route('/cursos', methods=['GET']) #obtener lista de cursos y sus datos básicos
    def get_cursos():
        code = 200
        #checkear cookies
        if session.get('user_id') is None:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        id_user = session.get('user_id')
        cursos = []

        try:
            user = User.query.filter_by(id=id_user).first()
            if user is None:
                code = 400
            else:
                cursos = Course.query.all()
                cursos = [curso.serialize() for curso in cursos]

            if len(cursos) == 0:
                code = 404

        except Exception as e:
            print(sys.exc_info())
            code = 500
        

        if code == 400:
            return jsonify({'success': False, 'message': 'User not found'}), 400
        elif code == 404:
            return jsonify({'success': False, 'message': 'Courses not found'}), 404
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'courses': cursos}), 200

    @app.route('/cursos/<string:curso_id>', methods=['GET']) #obtener curso y sus alumnos
    def get_curso(curso_id):
        code = 200
        #checkear cookies
        if session.get('user_id') is None:
            return jsonify({'success': False, 'message': 'Unauthorized'}), 401
        
        id_user = session.get('user_id')

        try:
            user = User.query.filter_by(id=id_user).first()
            if user is None:
                code = 400
            else:
                curso = Course.query.filter_by(id_course=curso_id).first()
                if curso is None:
                    code = 404
                else:
                    alumnos = ATieneC.query.filter_by(id_course=curso_id).all()
                    alumnos = [alumno.id_student for alumno in alumnos]

                    curso = curso.serialize()
                    curso['students'] = alumnos
                
        except Exception as e:
            print(sys.exc_info())
            code = 500
        
        if code == 400:
            return jsonify({'success': False, 'message': 'User not found'}), 400
        elif code == 404:
            return jsonify({'success': False, 'message': 'Course not found'}), 404
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'course': curso}), 200

    @app.route('/cursos', methods=['POST']) #crear curso
    def add_course():
        code = 201
        #checkear cookies
        if session.get('user_id') is None:
            code = 401
        else:
            user_id = session.get('user_id')
            errorList = []

            try:
                if Teacher.query.filter_by(id=user_id).first() is None:
                    code = 403
                else:
                    data = request.get_json()
                    if "name" in data:
                        curso = Course.query.filter_by(course_name=data['name']).first()
                        if curso is None:
                            curso = Course(course_name=data['name'], id_teacher=user_id, created_at=datetime.now())
                            db.session.add(curso)
                            db.session.commit()
                        else:
                            code = 409
                    else:
                        errorList.append('Nombre del curso no especificado')
                        code = 400
            except Exception as e:
                print(sys.exc_info())
                code = 500


        if code == 400:
            return jsonify({'success': False, 'message': errorList}), 400
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Curso creado correctamente'}), code

    @app.route('/cursos/<string:curso_id>', methods=['DELETE']) #eliminar curso
    def delete_course(curso_id):
        code = 200
        #checkear cookies
        if session.get('user_id') is None:
            code = 401
        else:
            user_id = session.get('user_id')
            errorList = []

            try:
                confirmation = request.args.get('confirmation', None)
                if Teacher.query.filter_by(id=user_id).first() is None:
                    code = 403
                else:
                    curso = Course.query.filter_by(id_course=curso_id).first()
                    if curso is None:
                        code = 404
                    else:
                        if confirmation == curso.course_name:
                            #borrar relaciones, tareas, notas, etc
                            #notas
                            notas = Score.query.filter_by(id_course=curso_id).all()
                            for nota in notas:
                                db.session.delete(nota)
                            db.session.commit()

                            #tareas
                            tareas = Homework.query.filter_by(id_course=curso_id).all()
                            for tarea in tareas:
                                db.session.delete(tarea)
                            db.session.commit()

                            #relaciones
                            relaciones = ATieneC.query.filter_by(id_course=curso_id).all()
                            for relacion in relaciones:
                                db.session.delete(relacion)
                            db.session.commit()

                            #curso 
                            db.session.delete(curso)
                        else:
                            code = 400
                            errorList.append("Confirmation string not matching (should be course's name)")
                        
                        curso = curso.serialize()

            except Exception as e:
                print(sys.exc_info())
                code = 500

            if code == 400:
                return jsonify({'success': False, 'message': errorList}), 400
            elif code == 404:
                return jsonify({'success': False, 'message': 'Course not found'}), 404
            elif code != 200:
                abort(code)
            else:
                return jsonify({'success': True, 'message': 'Curso eliminado correctamente', 'curso': curso}), code

    @app.route('/courses/<string:teacher_id>', methods=['GET'])
    def get_teacher_courses(teacher_id):
        #checkear cookies
        if session.get('user_id') is None:
            abort(401)
        if User.query.filter_by(id=session.get('user_id')).first() is None:
            abort(403)
        
        try:
            teacher = Teacher.query.get(teacher_id)

            if teacher is None:
                return jsonify({'success': False, 'message': 'Profesor no encontrado'}), 404

            courses = Course.query.filter_by(id_teacher=teacher_id).all()

            course_data = [course.serialize() for course in courses]

            if len(course_data) == 0:
                return jsonify({'success': True, 'message': 'El profesor no tiene cursos asignados', 'courses': course_data}), 200
            else:
                return jsonify({'success': True, 'courses': course_data}), 200

        except Exception as e:
            abort(500)

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
