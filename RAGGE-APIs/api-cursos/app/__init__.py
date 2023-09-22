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
)

from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity, set_access_cookies, unset_jwt_cookies
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from sqlalchemy import ForeignKey
from flask_bcrypt import Bcrypt
from flask import make_response


import sys
import uuid
import json
import os
from datetime import datetime
from flask_bcrypt import Bcrypt
from datetime import timedelta


# App

def create_app(test_config=None):
    app = Flask(__name__)
    app.secret_key = 'pneumonoultramicroscopicsilicovolcanoconiosis'
    app.config['JWT_SECRET_KEY'] = 'pneumonoultramicroscopicsilicovolcanoconiosis'
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    bcrypt = Bcrypt(app)
    jwt = JWTManager(app)

    with app.app_context():
        setup_db(app, test_config['database_path'] if test_config else None)
        CORS(app, origins=['http://localhost:8081'], supports_credentials=True)
        create_default_data(app, db)

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,POST,DELETE,OPTIONS')
        return response

    # ROUTES API -----------------------------------------------------------
    @app.route('/cursos', methods=['GET'])
    def get_cursos():
        returned_code = 200
        error_message = ''
        cursos_list = []

        try:
            search_query = request.args.get('search', None)
            if search_query:
                cursos = Course.query.filter(
                    Course.name.like('%{}%'.format(search_query))).all()
                cursos_list = [curso.serialize() for curso in cursos]

            else:
                cursos = Course.query.all()
                cursos_list = [curso.serialize() for curso in cursos]

            if not cursos_list:
                returned_code = 404
                error_message = 'No course found'

        except Exception as e:
            returned_code = 500
            error_message = 'Error retrieving courses'

        if returned_code != 200:
            return jsonify({'success': False, 'message': error_message}), returned_code

        return jsonify({'success': True, 'cursos': cursos_list}), returned_code

    @app.route('/cursos', methods=['POST'])
    def add_course():
        try:
            data = requests.get_json()

            if 'course_name' not in data or 'id_course' not in data:
                return jsonify({'success': False, 'message': 'Los campos course_name y course_code son requeridos'}), 400

            new_course = Course(course_name=data['course_name']=data['code_course'])

            db.session.add(new_course)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Curso agregado correctamente'}), 201

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error al agregar el curso'}), 500

    @app.route('/cursos/<string:curso_id>', methods=['DELETE'])
    def delete_course(curso_id):
        try:
            corso = Course.query.get(curso_id)

            if not curso:
                return jsonify({'success': False, 'message': 'Course not found'}), 404

            db.session.delete(curso)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Curso deleted successfully'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error deleting curso'}), 500
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
