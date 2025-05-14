from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
load_dotenv()


app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.abspath(os.path.join(basedir, '..', 'db', 'database.db'))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Логін-менеджер
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Модель користувача
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True, nullable=False)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(10), default='user')  # або 'admin'

# Завантаження користувача
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Головна сторінка
@app.route('/')
def index():
    return render_template('index.html')

# Реєстрація
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_pw = generate_password_hash(password, method='pbkdf2:sha256')

        if User.query.filter_by(email=email).first():
            flash('У вас вже є акаунт з цим email.')
            return redirect(url_for('register'))

        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Успішна реєстрація!')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Невірний логін або пароль')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard():
    return f"Привіт, {current_user.username}!"

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/admin/add-animal', methods=['GET', 'POST'])
@login_required
def add_animal():
    if current_user.role != 'admin':
        abort(403)

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        gender = request.form['gender']
        description = request.form['description']
        status = request.form['status']
        photo_url = request.form['photo_url']

        new_animal = Animal(
            name=name,
            species=species,
            age=age,
            gender=gender,
            description=description,
            status=status,
            photo_url=photo_url
        )
        db.session.add(new_animal)
        db.session.commit()
        flash('Тваринку додано успішно!')
        return redirect(url_for('search_animals'))  # твоя сторінка зі списком тварин

    return render_template('add_animal.html')

# Запуск
if __name__ == '__main__':
    # Переконайся, що база створена
    if not os.path.exists('../db/database.db'):
        os.makedirs('../db', exist_ok=True)

    with app.app_context():
        db.create_all()

        # Створити адміністратора, якщо не існує
        admin_email = os.getenv("ADMIN_EMAIL")
        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password = os.getenv("ADMIN_PASSWORD")

        if not User.query.filter_by(email=admin_email).first():
            admin_user = User(
                username=admin_username,
                email=admin_email,
                password=generate_password_hash(admin_password, method='pbkdf2:sha256'),
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("🔐 Адміністратора створено!")

    app.run(debug=True)
