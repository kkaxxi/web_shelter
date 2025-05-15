from flask import render_template, redirect, url_for, request, flash, abort, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os, uuid
from PIL import Image
from . import animals_bp
from models import db, Animal, Favorite
from forms import AnimalForm, DummyForm

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

            # Compress
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


@animals_bp.route('/toggle-favorite/<int:animal_id>', methods=['POST'])
@login_required
def toggle_favorite(animal_id):
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

@animals_bp.route('/animal/<int:animal_id>')
def animal_detail(animal_id):
    animal = Animal.query.get_or_404(animal_id)
    return render_template('animal_detail.html', animal=animal)

