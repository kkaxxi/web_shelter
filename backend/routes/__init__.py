from flask import Blueprint

auth_bp = Blueprint('auth', __name__)
animals_bp = Blueprint('animals', __name__)
help_bp = Blueprint('help', __name__)
reports_bp = Blueprint('reports', __name__)

from . import auth, animals, help, reports  
