from flask import render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os, uuid
from PIL import Image
from datetime import datetime, timedelta

from . import animals_bp
from models import db, Animal, Favorite, AdoptionRequest, VolunteerRequest, Feedback, User
from forms import AnimalForm, DummyForm, AdoptionContractForm, AdoptionRequestForm, AdminAdoptionResponseForm, MessageFilterForm, AdoptionRequestFilterForm
from utils import send_email

# --- Пошук тварин ---
@animals_bp.route('/search')
def search_animals():
    species = request.args.get('species')
    gender = request.args.get('gender')
    min_age = request.args.get('min_age', 0, type=int)
    max_age = request.args.get('max_age', 100, type=int)
    size = request.args.get('size')
    status = request.args.get('status')

    query = Animal.query
    if species and species != 'any':
        query = query.filter_by(species=species)
    if gender and gender != 'any':
        query = query.filter_by(gender=gender)
    if size and size != 'any':
        query = query.filter_by(size=size)
    if status and status != 'any':
        query = query.filter_by(status=status)
    query = query.filter(Animal.age >= min_age, Animal.age <= max_age)
    animals = query.all()

    fav_ids = []
    if current_user.is_authenticated:
        fav_ids = [f.animal_id for f in Favorite.query.filter_by(user_id=current_user.id).all()]

    return render_template('search.html', animals=animals, user_fav_ids=fav_ids)

# --- Додавання тваринки ---
@animals_bp.route('/admin/add-animal', methods=['GET', 'POST'])
@login_required
def add_animal():
    if current_user.role != 'admin':
        abort(403)

    form = AnimalForm()
    if form.validate_on_submit():
        filename = ''
        if form.photo.data:
            filename = f"{uuid.uuid4().hex}_{secure_filename(form.photo.data.filename)}"
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(photo_path)

            image = Image.open(photo_path)
            image.thumbnail((800, 800))
            image.save(photo_path, optimize=True, quality=70)

        animal = Animal(
            name=form.name.data,
            species=form.species.data,
            age=form.age.data,
            gender=form.gender.data,
            size=form.size.data,
            status=form.status.data,
            description=form.description.data,
            photo_url=f"/static/uploads/{filename}" if filename else ''
        )
        db.session.add(animal)
        db.session.commit()
        flash("Тварину додано")
        return redirect(url_for('animals.search_animals'))

    return render_template('add_animal.html', form=form)

# --- Редагування тваринки ---
@animals_bp.route('/admin/edit-animal/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def edit_animal(animal_id):
    if current_user.role != 'admin':
        abort(403)

    animal = Animal.query.get_or_404(animal_id)
    form = AnimalForm(obj=animal)

    if form.validate_on_submit():
        animal.name = form.name.data
        animal.species = form.species.data
        animal.age = form.age.data
        animal.gender = form.gender.data
        animal.size = form.size.data
        animal.status = form.status.data
        animal.description = form.description.data

        if form.photo.data:
            if animal.photo_url.startswith('/static/uploads/'):
                old_path = os.path.join(current_app.root_path, animal.photo_url.strip('/'))
                if os.path.exists(old_path):
                    os.remove(old_path)

            filename = f"{uuid.uuid4().hex}_{secure_filename(form.photo.data.filename)}"
            photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            form.photo.data.save(photo_path)

            image = Image.open(photo_path)
            image.thumbnail((800, 800))
            image.save(photo_path, optimize=True, quality=70)

            animal.photo_url = f"/static/uploads/{filename}"

        db.session.commit()
        flash("Тварину оновлено")
        return redirect(url_for('animals.search_animals'))

    return render_template('edit_animal.html', form=form, animal=animal)

# --- Видалення ---
@animals_bp.route('/admin/delete-animal/<int:animal_id>', methods=['POST'])
@login_required
def delete_animal(animal_id):
    if current_user.role != 'admin':
        abort(403)

    animal = Animal.query.get_or_404(animal_id)
    if animal.photo_url.startswith('/static/uploads/'):
        old_path = os.path.join(current_app.root_path, animal.photo_url.strip('/'))
        if os.path.exists(old_path):
            os.remove(old_path)

    db.session.delete(animal)
    db.session.commit()
    flash("Тварину видалено")
    return redirect(url_for('animals.search_animals'))

# --- Деталі тварини ---
@animals_bp.route('/animal/<int:animal_id>')
def animal_detail(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    return render_template('animal_detail.html', animal=animal)

# --- Завантаження договору ---
@animals_bp.route('/animals/<int:animal_id>/upload_contract', methods=['GET', 'POST'])
@login_required
def upload_contract(animal_id):
    if current_user.role != 'admin':
        abort(403)

    animal = Animal.query.get_or_404(animal_id)
    form = AdoptionContractForm()

    if form.validate_on_submit():
        file = form.contract.data
        filename = f"{animal.name.lower()}_{datetime.now().year}.pdf".replace(" ", "_")
        path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'contracts')
        os.makedirs(path, exist_ok=True)
        full_path = os.path.join(path, filename)
        file.save(full_path)

        animal.adoption_contract = f"contracts/{filename}"
        animal.status = 'усиновлено'
        db.session.commit()

        flash('✅ Договір збережено. Статус оновлено!')
        return redirect(url_for('animals.search_animals'))

    return render_template('upload_contract.html', form=form, animal=animal)

# --- Улюбленці ---
@animals_bp.route('/toggle-favorite/<int:animal_id>', methods=['POST'])
def toggle_favorite(animal_id):
    if not current_user.is_authenticated:
        flash("❌ Щоб додати улюбленця — увійдіть або зареєструйтесь.")
        return redirect(url_for('auth.login'))

    fav = Favorite.query.filter_by(user_id=current_user.id, animal_id=animal_id).first()
    if fav:
        db.session.delete(fav)
    else:
        db.session.add(Favorite(user_id=current_user.id, animal_id=animal_id))
    db.session.commit()
    return redirect(request.referrer or url_for('animals.search_animals'))

@animals_bp.route('/favorites')
@login_required
def favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    ids = [f.animal_id for f in favs]
    fav_animals = Animal.query.filter(Animal.id.in_(ids)).all() if ids else []
    form = DummyForm()
    return render_template('favorites.html', animals=fav_animals, user_fav_ids=ids, form=form)

# --- Правила усиновлення ---
@animals_bp.route('/adoption-rules')
def adoption_rules():
    return render_template('adoption_rules.html')

# --- Створення заявки на усиновлення ---
@animals_bp.route('/adopt/<int:animal_id>', methods=['GET', 'POST'])
@login_required
def adopt_animal(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    form = AdoptionRequestForm()

    if form.validate_on_submit():
        interview_dt = datetime.strptime(form.preferred_datetime.data, "%Y-%m-%d %H:%M")
        new_request = AdoptionRequest(
            user_id=current_user.id,
            animal_id=animal.id,
            preferred_datetime=interview_dt,
            comment=form.comment.data
        )
        db.session.add(new_request)
        db.session.commit()
        flash("✅ Заявку на усиновлення надіслано. Очікуйте відповідь менеджера.")
        return redirect(url_for('animals.animal_detail', animal_id=animal.id))

    return render_template('adoption_form.html', form=form, animal=animal)

# --- Перегляд усіх заявок (адмін) ---
@animals_bp.route('/admin/adoption-requests', methods=['GET'])
@login_required
def view_adoption_requests():
    if current_user.role != 'admin':
        abort(403)

    form = AdoptionRequestFilterForm(request.args)

    query = AdoptionRequest.query.join(User).join(Animal)

    if form.user_name.data:
        query = query.filter(User.username.ilike(f"%{form.user_name.data}%"))

    if form.animal_name.data:
        query = query.filter(Animal.name.ilike(f"%{form.animal_name.data}%"))

    if form.status.data and form.status.data != '':
        query = query.filter(AdoptionRequest.interview_status == form.status.data)

    requests = query.order_by(AdoptionRequest.timestamp.desc()).all()

    return render_template('admin_list.html', requests=requests, form=form, mode="adoption")


# --- Обробка однієї заявки ---
@animals_bp.route('/admin/adoptions/<int:req_id>', methods=['GET', 'POST'])
@login_required
def manage_adoption_request(req_id):
    if current_user.role != 'admin':
        abort(403)

    req = AdoptionRequest.query.get_or_404(req_id)
    form = AdminAdoptionResponseForm()

    if request.method == 'GET':
        form.interview_status.data = req.interview_status
        form.reply.data = req.reply

    if form.validate_on_submit():
        req.interview_status = form.interview_status.data
        req.reply = form.reply.data
        db.session.commit()

        send_email(
            to=req.user.email,
            subject="Відповідь на заявку на усиновлення",
            body=f"Привіт, {req.user.username}!\n\n"
                 f"Ваша заявка на тваринку {req.animal.name} отримала статус: {req.interview_status.upper()}.\n\n"
                 f"Коментар адміністратора:\n{req.reply}\n\n"
                 f"З найкращими побажаннями,\nКоманда притулку"
        )

        flash("✅ Відповідь збережено та надіслано на email користувача.")
        return redirect(url_for('animals.view_adoption_requests'))

    return render_template("admin_reply.html", form=form, data=req, mode="adoption")


@animals_bp.route('/messages')
@login_required
def view_messages():
    form = MessageFilterForm(request.args)
    section = form.section.data or "all"

    adoption_msgs = AdoptionRequest.query.filter_by(user_id=current_user.id).filter(AdoptionRequest.reply.isnot(None)).all()
    volunteer_msgs = VolunteerRequest.query.filter_by(user_id=current_user.id).filter(VolunteerRequest.reply.isnot(None)).all()
    feedback_msgs = Feedback.query.filter_by(email=current_user.email).filter(Feedback.reply.isnot(None)).all()

    return render_template(
        "user_messages.html",
        form=form,
        section=section,
        adoption_msgs=adoption_msgs,
        volunteer_msgs=volunteer_msgs,
        feedback_msgs=feedback_msgs
    )

