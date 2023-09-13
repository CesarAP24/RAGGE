import unittest  # libreria de python para realizar test
from app.models import *
from app import create_app
from flask_sqlalchemy import SQLAlchemy
import json
import random
from config.qa import config

class RaggeTests(unittest.TestCase):
	def setUp(self):
		print(self)
		database_path = config["DATABASE_URI"]
		self.app = create_app({'database_path': database_path})
		self.client = self.app.test_client()
