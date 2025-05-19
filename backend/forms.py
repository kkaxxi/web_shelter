from flask_wtf import FlaskForm 
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, SubmitField, IntegerField,
    TextAreaField, SelectField, BooleanField, FileField,
    DateField, TimeField, SubmitField

)
from wtforms.validators import DataRequired, Email, NumberRange, Optional
from datetime import datetime, timedelta

class RegisterForm(FlaskForm):
    username = StringField('Ім’я', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Зареєструватись')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    submit = SubmitField('Увійти')

class DonationForm(FlaskForm):
    amount = IntegerField('Сума', validators=[DataRequired(), NumberRange(min=1)])
    is_monthly = BooleanField('Щомісячна підтримка')
    submit = SubmitField('Задонатити')

class FeedbackForm(FlaskForm):
    name = StringField('Ім’я', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    message = TextAreaField('Повідомлення', validators=[DataRequired()])
    submit = SubmitField('Надіслати')

class FeedbackReplyForm(FlaskForm):
    reply = TextAreaField("Відповідь", validators=[DataRequired()])
    submit = SubmitField("Надіслати відповідь")


class VolunteerForm(FlaskForm):
    help_type = SelectField(
        'Спосіб допомоги',
        choices=[
            ('догляд', 'Догляд за тваринами'),
            ('розповсюдження', 'Поширення інформації'),
            ('інші', 'Інше')
        ],
        validators=[DataRequired()]
    )
    email = StringField('Email', validators=[Optional(), Email()])
    comment = TextAreaField('Коментар (необов’язково)', validators=[Optional()])
    submit = SubmitField('Надіслати')

class AnimalForm(FlaskForm):
    name = StringField("Ім’я", validators=[DataRequired()])
    species = StringField("Вид", validators=[DataRequired()])
    age = IntegerField("Вік", validators=[DataRequired(), NumberRange(min=0)])
    gender = SelectField("Стать", choices=[("male", "Ч"), ("female", "Ж")], validators=[DataRequired()])
    size = SelectField("Розмір", choices=[("small", "Малий"), ("medium", "Середній"), ("large", "Великий")], validators=[DataRequired()])
    status = SelectField("Статус", choices=[("в притулку", "в притулку"), ("усиновлено", "усиновлено")], validators=[DataRequired()])
    description = TextAreaField("Опис", validators=[Optional()])
    photo = FileField("Фото (jpg/png)", validators=[Optional()])
    submit = SubmitField("Зберегти")

class DummyForm(FlaskForm):
    submit = SubmitField('')  # пустий submit

class MonthlyReportForm(FlaskForm):
    year = IntegerField('Рік', validators=[DataRequired()])
    month = StringField('Місяць', validators=[DataRequired()])
    month_number = IntegerField('Номер місяця (1-12)', validators=[DataRequired(), NumberRange(min=1, max=12)])

    income = IntegerField('Надходження')
    expenses = IntegerField('Витрати')
    
    operating_costs = IntegerField('Функціонування притулку')
    vet_services = IntegerField('Ветеринарні послуги/препарати')
    garbage = IntegerField('Вивіз сміття')
    salary = IntegerField('Заробітна плата')
    dry_food = IntegerField('Сухий корм')
    cat_litter = IntegerField('Котячий наповнювач')
    grains = IntegerField('Екструдований корм та крупи')
    construction = IntegerField('Будматеріали')

    adopted_animals = IntegerField('Усиновлено тварин')
    new_animals = IntegerField('Нові тварини')
    submit = SubmitField('Додати звіт')


class AdoptionContractForm(FlaskForm):
    contract = FileField('Договір (PDF)', validators=[
        FileAllowed(['pdf'], 'Дозволено тільки PDF-файли'),
        DataRequired()
    ])
    submit = SubmitField('Завантажити')


class AdoptionRequestForm(FlaskForm):
    preferred_slot_id = SelectField(
        "Оберіть слот інтерв’ю",
        coerce=int,
        validators=[DataRequired()]
    )
    comment = TextAreaField("Коментар (необов'язково)", validators=[Optional()])
    submit = SubmitField("Надіслати заявку")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from models import InterviewSlot
        self.preferred_slot_id.choices = [
            (slot.id, slot.datetime.strftime("%d.%m.%Y %H:%M"))
            for slot in InterviewSlot.query.filter_by(is_taken=False).order_by(InterviewSlot.datetime).all()
        ]

class AdminAdoptionResponseForm(FlaskForm):
    interview_status = SelectField(
        "Статус заявки",
        choices=[
            ("approved", "✅ Схвалено"),
            ("rejected", "❌ Відхилено")
        ],
        validators=[DataRequired()]
    )

    reply = TextAreaField("Відповідь користувачу", validators=[DataRequired()])
    submit = SubmitField("💬 Надіслати відповідь")

class AdoptionRequestFilterForm(FlaskForm):
    user_name = StringField("Ім’я користувача", validators=[Optional()])
    animal_name = StringField("Ім’я тварини", validators=[Optional()])
    status = SelectField('Статус', choices=[
    ('', 'Усі'),
    ('pending', 'Очікує'),
    ('approved', 'Схвалено'),
    ('rejected', 'Відхилено')
    ], default='')

    submit = SubmitField("🔍 Фільтрувати")


class MessageFilterForm(FlaskForm):
    section = SelectField("Фільтр", choices=[
        ("all", "Усі"),
        ("adoption", "Заявки на усиновлення"),
        ("volunteer", "Волонтерство"),
        ("feedback", "Зворотний зв’язок")
    ])
    submit = SubmitField("🔍 Показати")


class InterviewSlotForm(FlaskForm):
    date = DateField("Дата", format="%Y-%m-%d", validators=[DataRequired()])
    time = TimeField("Час", format="%H:%M", validators=[DataRequired()])
    submit = SubmitField("Додати слот")