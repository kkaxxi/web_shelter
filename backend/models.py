from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime  

db = SQLAlchemy()
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
    adoption_contract = db.Column(db.String(300), nullable=True)  # шлях до PDF



class Favorite(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    is_monthly = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    

class VolunteerRequest(db.Model):
    __tablename__ = 'volunteer_request'
    id = db.Column(db.Integer, primary_key=True)
    help_type = db.Column(db.String(100), nullable=False)
    comment = db.Column(db.Text, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    email = db.Column(db.String(150), nullable=True)
    reply = db.Column(db.Text, nullable=True)  # 🆕 ДОДАЙ ЦЕ
    user = db.relationship('User', backref='volunteer_requests')


class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    reply = db.Column(db.Text)  # 💬 відповідь адміністратора
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class MonthlyReport(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    year = db.Column(db.Integer, nullable=False)
    month = db.Column(db.String(20), nullable=False)
    month_number = db.Column(db.Integer, nullable=False)  # Наприклад: 1 = Січень, 2 = Лютий і т.д.

    
    income = db.Column(db.Integer, default=0)
    expenses = db.Column(db.Integer, default=0)

    # Витрати деталізовано
    operating_costs = db.Column(db.Integer, default=0)
    vet_services = db.Column(db.Integer, default=0)
    garbage = db.Column(db.Integer, default=0)
    salary = db.Column(db.Integer, default=0)
    dry_food = db.Column(db.Integer, default=0)
    cat_litter = db.Column(db.Integer, default=0)
    grains = db.Column(db.Integer, default=0)
    construction = db.Column(db.Integer, default=0)

    # Інше
    adopted_animals = db.Column(db.Integer, default=0)
    new_animals = db.Column(db.Integer, default=0)
    pdf_url = db.Column(db.String(300))

class AdoptionRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    animal_id = db.Column(db.Integer, db.ForeignKey('animal.id'), nullable=False)
    preferred_datetime = db.Column(db.DateTime, nullable=True)

    comment = db.Column(db.Text)
    interview_status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    appointment_datetime = db.Column(db.String(100), nullable=True)  # реальна зустріч
    video_link = db.Column(db.String(300), nullable=True)  # (опційно — посилання на Google Meet)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='adoption_requests')
    animal = db.relationship('Animal', backref='adoption_requests')

    reply = db.Column(db.Text, nullable=True)

