from flask import Flask, render_template
from flask_login import LoginManager
from flask_migrate import Migrate
from models import db, User
from dotenv import load_dotenv
import os
from flask_wtf.csrf import CSRFProtect
csrf = CSRFProtect()


from routes import auth_bp, animals_bp, help_bp, reports_bp

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, '..', 'db', 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# У app.py
REPORTS_FOLDER = os.path.join(basedir, 'static', 'reports')
app.config['REPORTS_FOLDER'] = REPORTS_FOLDER
os.makedirs(REPORTS_FOLDER, exist_ok=True)

CONTRACTS_FOLDER = os.path.join(basedir, 'static', 'contracts')
app.config['CONTRACTS_FOLDER'] = CONTRACTS_FOLDER
os.makedirs(CONTRACTS_FOLDER, exist_ok=True)


db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

app.register_blueprint(auth_bp)
app.register_blueprint(animals_bp)
app.register_blueprint(help_bp)
app.register_blueprint(reports_bp)

@app.route('/')
def index():
    return render_template("index.html")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)

