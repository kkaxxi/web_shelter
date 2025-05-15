from flask import render_template, redirect, url_for, flash
from flask_login import current_user
from . import help_bp
from models import db, Donation, Feedback, VolunteerRequest
from forms import DonationForm, FeedbackForm, VolunteerForm

@help_bp.route('/help', methods=['GET', 'POST'])
def help_page():
    donation_form = DonationForm()
    feedback_form = FeedbackForm()
    volunteer_form = VolunteerForm()

    # 🟢 Обробка донату
    if donation_form.submit.data and donation_form.validate_on_submit():
        donation = Donation(
            amount=donation_form.amount.data,
            is_monthly=donation_form.is_monthly.data,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(donation)
        db.session.commit()
        flash("Дякуємо за вашу підтримку!")
        return redirect(url_for('help.help_page'))

    # 🟢 Обробка зворотного зв'язку
    if feedback_form.submit.data and feedback_form.validate_on_submit():
        feedback = Feedback(
            name=feedback_form.name.data,
            email=feedback_form.email.data,
            message=feedback_form.message.data
        )
        db.session.add(feedback)
        db.session.commit()
        flash("Дякуємо за зворотний зв'язок!")
        return redirect(url_for('help.help_page'))

    # 🟢 Обробка волонтерства
    if volunteer_form.submit.data and volunteer_form.validate_on_submit():
        volunteer = VolunteerRequest(
            help_type=volunteer_form.help_type.data,
            comment=volunteer_form.comment.data,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(volunteer)
        db.session.commit()
        flash("Ваш запит волонтерства прийнято!")
        return redirect(url_for('help.help_page'))

    return render_template(
        'help.html',
        donation_form=donation_form,
        feedback_form=feedback_form,
        volunteer_form=volunteer_form
    )
