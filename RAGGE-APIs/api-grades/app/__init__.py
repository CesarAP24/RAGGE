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
    @app.route('/homework', methods=['GET'])
    def get_homework():
        returned_code = 200
        error_message = ''
        homework_list = []

        try:
            search_query = request.args.get('search', None)
            if search_query:
                homeworks = Homework.query.filter(
                    (Homework.name_homework.like('%{}%'.format(search_query))) |
                    (Homework.indications('%{}%'.format(search)))
                ).all()

                homework_list = [homework.serialize()
                                 for homework in homeworks]
            else:
                homeworks = Homework.query.all()
                homework_list = [homework.serialize()
                                 for homework in homeworks]

            if not homework_list:
                returned_code = 404
                error_message = 'Not homework found'

        except Exception as e:
            returned_code = 500
            error_message = 'Error retrieving homework'

        if returned_code != 200:
            return jsonify({'success': False, 'message': error_message}), returned_code

        return jsonify({'success': True, 'homework': homework_list}), returned_code

    @app.route('/homework', methods=['POST'])
    def create_homework():
        try:
            data = requests.get_json()
            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400
                name_homework = data.get('name_homwork')
                deadline = data.get('deadline')
                indications = data.get('indications')

            if not all([name_homework, deadline, indications]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400

            new_homework = Homework(
                name_homework=name_homework,
                deadline=deadline,
                indications=indications
            )

            db.session.add(new_homework)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Homework created successfully'}), 201

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error creating homework'}), 500

    @app.route('/homework/string:homework_id', methods=['DELETE'])
    def delete_homework(homework_id):
        try:
            homework = Homework.query.get(homework_id)

            if not homework:
                return jsonify({'success': False, 'message': 'Homework not found'}), 404

            db.session.delete(homework)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Homework deleted successfully'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error deleting homework'}), 500

    @app.route('/delibery/string:delibery_id', methods=['GET'])
    def get_delibery(delibery_id):
        try:
            delibery = Delibery.query.get(delibery_id)

            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404

            delibery_info = {
                'id' = delibery.id,
                'date' = delibery.date.strftime('%Y-%m-%d %H:%M:%S'),
                'id_homework': delibery.id_homework,
                'id_student': delibery.id_student,
                'route_archive': delibery.route_archive,
            }

            return jsonify({'success': True, 'delibery': delibery_info}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error retrieving delivery'}), 500

    @app.route('/delivery/<string:delivery_id>', methods=['PATCH'])
    def update_delivery(delivery_id):
        try:
            delivery = Delivery.query.get(delivery_id)

            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404

            data = request.get_json()

            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400

            if 'route_archive' in data:
                delivery.route_archive = data['route_archive']

            delivery.modified_at = datetime.utcnow()
            db.session.commit()

            return jsonify({'success': True, 'message': 'Delivery updated successfully'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error updating delivery'}), 500

    @app.route('/delivery/<string:delivery_id>', methods=['DELETE'])
    def delete_delivery(delivery_id):
        try:
            delivery = Delivery.query.get(delivery_id)

            if not delivery:
                return jsonify({'success': False, 'message': 'Delivery not found'}), 404

            db.session.delete(delivery)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Delivery deleted successfully'}), 200

        except Exception as e:

            return jsonify({'success': False, 'message': 'Error deleting delivery'}), 500

    @app.route('/score/<string:score_id>', methods=['GET'])
    def get_score(score_id):
        try:
            score = Score.query.get(score_id)

            if not score:
                return jsonify({'success': False, 'message': 'Score not found'}), 404

            score_info = score.serialize()

            return jsonify({'success': True, 'score': score_info}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error retrieving score'}), 500

    @app.route('/score', methods=['POST'])
    def create_score():
        try:
            data = request.get_json()

            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400

            date = data.get('date')
            id_homework = data.get('id_homework')
            id_student = data.get('id_student')
            value = data.get('value')

            if not all([date, id_homework, id_teacher, id_student, id_course, value]):
                return jsonify({'success': False, 'message': 'Missing required fields'}), 400

            new_score = Score(
                date=date,
                id_homework=id_homework,
                id_student=id_student,
                value=value
            )

            db.session.add(new_score)
            db.session.commit()

            return jsonify({'success': True, 'message': 'Score created successfully'}), 201

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error creating score'}), 500

    @app.route('/score/<string:score_id>', methods=['PATCH'])
    def update_score(score_id):
        try:
            score = Score.query.get(score_id)

            if not score:
                return jsonify({'success': False, 'message': 'Score not found'}), 404

            data = request.get_json()

            if not data:
                return jsonify({'success': False, 'message': 'Invalid JSON data'}), 400

            if 'value' in data:
                score.value = data['value']

            score.modified_at = datetime.utcnow()
            db.session.commit()

            return jsonify({'success': True, 'message': 'Score updated successfully'}), 200

        except Exception as e:
            return jsonify({'success': False, 'message': 'Error updating score'}), 500

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
