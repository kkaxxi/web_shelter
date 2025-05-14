from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv
load_dotenv()
from werkzeug.utils import secure_filename
from PIL import Image
import uuid



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

class Animal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    species = db.Column(db.String(50), nullable=False)  # Вид
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    size = db.Column(db.String(20))  
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='в притулку')  # або "усиновлено"
    photo_url = db.Column(db.String(300))  # Посилання на фото

UPLOAD_FOLDER = os.path.join(basedir, '..', 'static', 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024  # 2MB
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    return redirect(url_for('index'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/search')
def search_animals():
    animals = Animal.query.all()
    return render_template('search.html', animals=animals)


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
        size = request.form['size']
        status = request.form['status']
        description = request.form['description']

        if int(age) < 0:
            flash("Вік не може бути менше 0")
            return redirect(url_for('add_animal'))

        photo_file = request.files.get('photo')
        photo_url = ''
        if photo_file and photo_file.filename != '':
            filename = f"{uuid.uuid4().hex}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', filename)
            full_path = os.path.join(app.root_path, photo_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            image = Image.open(photo_file)
            image.thumbnail((800, 800))
            image.save(full_path, optimize=True, quality=70)

            photo_url = '/' + photo_path.replace('\\', '/')

        new_animal = Animal(
            name=name,
            species=species,
            age=age,
            gender=gender,
            size=size,
            status=status,
            photo_url=photo_url,
            description=description
        )
        db.session.add(new_animal)
        db.session.commit()
        flash('Тваринку додано успішно!')
        return redirect(url_for('search_animals'))

    return render_template('add_animal.html')

@app.route('/admin/edit-animal/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def edit_animal(animal_id):
    if current_user.role != 'admin':
        abort(403)

    animal = Animal.query.get_or_404(animal_id)

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        age = request.form['age']
        gender = request.form['gender']
        size = request.form['size']
        status = request.form['status']
        description = request.form['description']

        if int(age) < 0:
            flash("Вік не може бути менше 0")
            return redirect(url_for('edit_animal', animal_id=animal_id))

        animal.name = name
        animal.species = species
        animal.age = age
        animal.gender = gender
        animal.size = size
        animal.status = status
        animal.description = description

        photo_file = request.files.get('photo')
        if photo_file and photo_file.filename != '':
            # 🧹 Видалити попереднє фото (тільки якщо воно локальне)
            if animal.photo_url and animal.photo_url.startswith('/static/uploads/'):
                old_path = os.path.join(app.root_path, animal.photo_url.strip('/'))
                if os.path.exists(old_path):
                    os.remove(old_path)

            # 📥 Зберегти нове фото
            filename = f"{uuid.uuid4().hex}_{photo_file.filename}"
            photo_path = os.path.join('static/uploads', filename)
            full_path = os.path.join(app.root_path, photo_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)

            image = Image.open(photo_file)
            image.thumbnail((800, 800))
            image.save(full_path, optimize=True, quality=70)

            animal.photo_url = '/' + photo_path.replace('\\', '/')

        db.session.commit()
        flash("Зміни збережено")
        return redirect(url_for('search_animals'))

    return render_template('edit_animal.html', animal=animal)

@app.route('/admin/delete-animal/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id):
    if current_user.role != 'admin':
        abort(403)

    animal = Animal.query.get_or_404(animal_id)

    # 🧹 Видалення фото, якщо воно локальне (у static/uploads)
    if animal.photo_url and animal.photo_url.startswith('/static/uploads/'):
        photo_path = os.path.join(app.root_path, animal.photo_url.strip('/'))
        if os.path.exists(photo_path):
            os.remove(photo_path)

    db.session.delete(animal)
    db.session.commit()
    flash("Тварину успішно видалено!")
    return redirect(url_for('search_animals'))



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
