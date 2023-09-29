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
        CORS(app, origins="*", supports_credentials=True)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # ROUTES API -----------------------------------------------------------
    @app.route('/courses', methods=['GET']) #obtener lista de cursos y sus datos básicos
    def get_cursos():
        code = 200
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if User.query.filter_by(id=cookie).first() is None:
            abort(403)

        id_user = cookie;
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

    @app.route('/courses/<curso_id>', methods=['GET']) #obtener curso y sus alumnos
    def get_curso(curso_id):
        code = 200
        message = ""
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        id_user = cookie

        try:
            user = User.query.filter_by(id=id_user).first()
            if user is None:
                code = 400
                message = 'Cookie is not valid'
            else:
                curso = Course.query.filter_by(id_course=curso_id).first()
                if curso is None:
                    code = 404
                    message = 'Course not found'
                else:
                    alumnos = ATieneC.query.filter_by(id_curso=curso_id).all()
                    alumnos = [alumno.id_student for alumno in alumnos]

                    curso = curso.serialize()
                    curso['students'] = alumnos
                
        except Exception as e:
            print(sys.exc_info())
            code = 500
        
        if code == 400:
            return jsonify({'success': False, 'message': message}), 400
        elif code == 404:
            return jsonify({'success': False, 'message': message}), 404
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'course': curso}), 200

    @app.route('/courses', methods=['POST']) #crear curso
    def add_course():
        code = 201
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]

        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)
        
        user_id = cookie
        errorList = []

        try:
            data = request.get_json()
            if "name" in data:
                curso = Course.query.filter_by(course_name=data['name']).first()
                if curso:
                    code = 409
                    errorList.append('Ya existe un curso con ese nombre')
                else:
                    curso = Course(course_name=data['name'], id_teacher=user_id, created_at=datetime.now())
                    db.session.add(curso)
                    db.session.commit()
            else:
                errorList.append('Nombre del curso no especificado')
                code = 400
        except Exception as e:
            print(sys.exc_info())
            code = 500


        if code == 400:
            return jsonify({'success': False, 'message': errorList}), 400
        elif code == 409:
            return jsonify({'success': False, 'message': errorList}), 409
        elif code != 201:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Curso creado correctamente'}), code

    @app.route('/courses/<curso_id>', methods=['DELETE']) #eliminar curso
    def delete_course(curso_id):
        code = 200
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]
        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)
        
        errorList = []

        try:
            confirmation = request.json.get('confirmation')

            if confirmation is None:
                code = 400
                errorList.append("Confirmation string not found ('confirmation') ")

            curso = Course.query.filter_by(id_course=curso_id).first()

            if not(curso):
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
                    relaciones = ATieneC.query.filter_by(id_curso=curso_id).all()
                    for relacion in relaciones:
                        db.session.delete(relacion)
                    db.session.commit()

                    #curso 
                    db.session.delete(curso)
                    db.session.commit()
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

    @app.route('/teachers/<teacher_id>/courses', methods=['GET'])
    def get_teacher_courses(teacher_id):
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]

        if User.query.filter_by(id=cookie).first() is None:
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

    @app.route('/courses/<curso_id>/students', methods=['GET']) #obtener lista de alumnos de un curso
    def get_curso_students(curso_id):
        code = 200
        message = ""
        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)
        
        cookie = request.headers.get('Authorization').split(' ')[1]

        if User.query.filter_by(id=cookie).first() is None:
            abort(403)
        
        try:
            curso = Course.query.filter_by(id_course=curso_id).first()
            if curso is None:
                code = 404
                message = 'Course not found'
            else:
                alumnos = ATieneC.query.filter_by(id_curso=curso_id).all()
                alumnos = [alumno.id_alumno for alumno in alumnos]
                alumnos = [User.query.filter_by(id=alumno).first().serialize() for alumno in alumnos]

                #quitar contraseña
                for alumno in alumnos:
                    alumno.pop('contrasena')

                if len(alumnos) == 0:
                    code = 404
                    message = 'Students not found'

        except Exception as e:
            print(sys.exc_info())
            code = 500

        if code == 404:
            return jsonify({'success': False, 'message': message}), 404
        elif code != 200:
            abort(code)
        else:
            return jsonify({'success': True, 'students': alumnos, 'course': curso.serialize()}), 200

    @app.route('/courses/<curso_id>/students', methods=['POST']) #añadir alumno a un curso
    def add_student_to_course(curso_id):
        code = 201

        #checkear cookies
        if request.headers.get('Authorization') is None:
            abort(401)

        cookie = request.headers.get('Authorization').split(' ')[1]

        if Teacher.query.filter_by(id=cookie).first() is None:
            abort(403)
        
        errorList = []

        try:
            try:
                data = request.get_json()
            except:
                return jsonify({'success': False, 'message': 'Invalid JSON'}), 400

            if "id_student" in data:
                curso = Course.query.filter_by(id_course=curso_id).first()
                if curso is None:
                    code = 404
                    errorList.append('Course not found')
                else:
                    alumno = User.query.filter_by(id=data['id_student']).first()
                    if alumno:
                        relacion = ATieneC.query.filter_by(id_curso=curso_id, id_alumno=data['id_student']).first()
                        if relacion:
                            code = 409
                            errorList.append('Student already in course')
                        else:
                            relacion = ATieneC(id_curso=curso_id, id_alumno=data['id_student'])
                            db.session.add(relacion)
                            db.session.commit()
                    else:
                        code = 404
                        errorList.append('Student not found')
            else:
                errorList.append('Student id not specified (id_student)')
                code = 400

        except Exception as e:
            print(sys.exc_info())
            code = 500
            db.session.rollback()
        
        if code == 400:
            return jsonify({'success': False, 'message': errorList}), 400
        elif code == 404:
            return jsonify({'success': False, 'message': errorList}), 404
        elif code != 201:
            abort(code)
        else:
            return jsonify({'success': True, 'message': 'Student added to course'}), code

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
