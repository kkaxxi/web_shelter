from flask_wtf import FlaskForm 
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import (
    StringField, PasswordField, SubmitField, IntegerField,
    TextAreaField, SelectField, BooleanField, FileField
)
from wtforms.validators import DataRequired, Email, NumberRange, Optional

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