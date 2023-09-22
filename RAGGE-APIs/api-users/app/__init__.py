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
@dev.route()
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
    @dev.route('/register', methods=['POST'])
    def register():
        returned_code = 201
        list_error = []
        try:
            body = request.json

            if 'dni' not in body:
                list_error.append('dni')
            else:
                firstname = body['firstname']

            if 'firstname' not in body:
                list_error.append('firstname')
            else:
                firstname = body['firstname']

            if 'lastname' not in body:
                list_error.append('lastname')
            else:
                lastname = body['lastname']

            if 'contrasena' not in body:
                list_error.append('contrasena')
            else:
                contrasena = body['contrasena']

            if 'email' not in body:
                list_error.append('email')
            else:
                email = body['email']

            if len(list_error) > 0:
                returned_code = 400
            else:
                user = User(
                    dni=dni, firstname=firstname, lastname=lastname, email=email, contrasena=contrasena)
                db.session.add(user)
                db.session.commit()
                user_id = user.id

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500

        finally:
            db.session.close()

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error registering user', 'errors': list_errors}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'id': user_id, 'success': True, 'message': 'User registered successfully!'}), returned_code

    @dev.route('/login', methods=['POST'])
    def login():
        return_code = 200
        list_error = []

        try:
            body = request.json
            if 'dni' not in body:
                list_error.append('dni is required to login')
            else:
                dni = body['dni']

            if 'contrasena' not in body:
                list_error.append('password is required to login')

            else:
                contrasena = bod['contrasena']

                if len(list_error) > 0:
                    return_code = 400

                else:
                    user = User.query.filter_by(dni=dni).first()

                    if user and user.check_contrasena(contrasena):
                    access_token = create_access_token(identity=user.id_user)
                    returned_code = 200
                else:
                    returned_code = 401
                    list_errors.append('Cliente o contraseña incorrectos')

        except Exception as e:
            print(sys.exc_info())
            db.session.rollback()
            returned_code = 500
        finally:
            db.session.close()

        if returned_code == 400:
            return jsonify({'success': False, 'message': 'Error en la autenticación', 'errors': list_errors}), returned_code
        elif returned_code != 201:
            abort(returned_code)
        else:
            return jsonify({'success': True, 'message': 'Autenticación exitosa', 'token': 'tu_token_de_acceso'}), returned_code

    @dev.route('/student', methods=['GET'])
    def get_students():
        returned_code = 200
        error_message = ''
        students_list = []

        try:
            search_query = request.args.get('search', None)
            if search_query:
                students = Student.query.filter(
                Student.firstname.like('%{}%'.format(search_query))).all()

               students_list = [student.serialize() for student in students]

            else:
                students = User.query.all()
                student_list = [student.serialize() for student in students]

            if not students_list:
                returned_code = 404
                error_message = 'No students found'

        except Exception as e:
            print(sys.exc_info())
            returned_code = 500
            error_message = 'Error retrieving students'

        if returned_code != 200:
            return jsonify({'success': False, 'message': error_message}), returned_code

        return jsonify({'success': True, 'students': profesores_list}), returned_code

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
