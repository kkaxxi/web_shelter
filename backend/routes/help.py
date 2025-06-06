from flask import render_template, redirect, url_for, flash, abort, request
from flask_login import current_user, login_required
from . import help_bp
from models import db, Donation, Feedback, VolunteerRequest, User
from forms import DonationForm, FeedbackForm, VolunteerForm, FeedbackReplyForm
from sqlalchemy import or_

# 🟢 Обробники форм
def handle_donation_form(form):
    if form.submit.data and form.validate_on_submit():
        donation = Donation(
            amount=form.amount.data,
            is_monthly=form.is_monthly.data,
            user_id=current_user.id if current_user.is_authenticated else None
        )
        db.session.add(donation)
        db.session.commit()
        flash("Дякуємо за вашу підтримку!")
        return True
    return False

def handle_feedback_form(form):
    if form.submit.data and form.validate_on_submit():
        feedback = Feedback(
            name=form.name.data,
            email=form.email.data,
            message=form.message.data
        )
        db.session.add(feedback)
        db.session.commit()
        flash("Дякуємо за зворотний зв’язок!")
        return True
    return False

def handle_volunteer_form(form):
    if form.submit.data and form.validate_on_submit():
        volunteer = VolunteerRequest(
            help_type=form.help_type.data,
            comment=form.comment.data,
            user_id=current_user.id if current_user.is_authenticated else None,
            email=current_user.email if current_user.is_authenticated else form.email.data  # 🆕
        )
        db.session.add(volunteer)
        db.session.commit()
        flash("Ваш запит волонтерства прийнято!")
        return True
    return False


# 🏠 Головна сторінка допомоги
@help_bp.route('/help', methods=['GET', 'POST'])
def help_page():
    donation_form = DonationForm()
    feedback_form = FeedbackForm()
    volunteer_form = VolunteerForm()

    if handle_donation_form(donation_form) or \
       handle_feedback_form(feedback_form) or \
       handle_volunteer_form(volunteer_form):
        return redirect(url_for('help.help_page'))

    return render_template(
        'help.html',
        donation_form=donation_form,
        feedback_form=feedback_form,
        volunteer_form=volunteer_form
    )


@help_bp.route('/help/messages')
@login_required
def view_all_messages():
    if current_user.role != 'admin':
        abort(403)

    show = request.args.get('show', 'all')  # all / feedback / volunteer
    show_unanswered = request.args.get('unanswered') == '1'
    sort_order = request.args.get('sort', 'desc')

    if show == 'volunteer':
        query = VolunteerRequest.query
        if show_unanswered:
            query = query.filter((VolunteerRequest.reply == None) | (VolunteerRequest.reply == ''))
        query = query.order_by(VolunteerRequest.timestamp.asc() if sort_order == 'asc' else VolunteerRequest.timestamp.desc())
        requests = query.all()
        return render_template('admin_list.html', requests=requests, mode='volunteer')

    elif show == 'feedback':
        query = Feedback.query
        if show_unanswered:
            query = query.filter((Feedback.reply == None) | (Feedback.reply == ''))
        query = query.order_by(Feedback.timestamp.asc() if sort_order == 'asc' else Feedback.timestamp.desc())
        requests = query.all()
        return render_template('admin_list.html', requests=requests, mode='feedback')

    else:
        # Об'єднуємо всі повідомлення у один список з тегом типу
        volunteer = VolunteerRequest.query.order_by(VolunteerRequest.timestamp.desc()).all()
        feedback = Feedback.query.order_by(Feedback.timestamp.desc()).all()
        combined = [
            *[{'type': 'volunteer', 'obj': v} for v in volunteer],
            *[{'type': 'feedback', 'obj': f} for f in feedback]
        ]
        # Можна відсортувати об'єднано
        combined.sort(key=lambda x: x['obj'].timestamp, reverse=(sort_order == 'desc'))
        return render_template('admin_list.html', combined_requests=combined, mode='all')





@help_bp.route('/help/volunteer_reply/<int:volunteer_id>', methods=['GET', 'POST'])
@login_required
def reply_volunteer(volunteer_id):
    if current_user.role != 'admin':
        abort(403)

    volunteer = VolunteerRequest.query.get_or_404(volunteer_id)
    form = FeedbackReplyForm(reply=volunteer.reply)

    if form.validate_on_submit():
        volunteer.reply = form.reply.data
        db.session.commit()
        flash("✅ Відповідь збережено!")
        return redirect(url_for('help.view_all_messages'))

    return render_template("admin_reply.html", form=form, data=volunteer, mode="volunteer")



# ✍️ Відповідь на конкретне повідомлення
@help_bp.route('/help/feedbacks/<int:feedback_id>', methods=['GET', 'POST'])
@login_required
def reply_feedback(feedback_id):
    if current_user.role != 'admin':
        abort(403)

    feedback = Feedback.query.get_or_404(feedback_id)
    form = FeedbackReplyForm(reply=feedback.reply)

    if form.validate_on_submit():
        feedback.reply = form.reply.data
        db.session.commit()
        flash("✅ Відповідь збережено!")
        return redirect(url_for('help.view_all_messages'))

    return render_template("admin_reply.html", form=form, data=feedback, mode="feedback")



# 👀 Перегляд відповіді за email
@help_bp.route('/help/feedback_status/<string:email>')
def feedback_status(email):
    feedbacks = Feedback.query.filter_by(email=email).order_by(Feedback.timestamp.desc()).all()
    volunteers = VolunteerRequest.query.join(User).filter(User.email == email).order_by(VolunteerRequest.timestamp.desc()).all()

    return render_template(
        'user_messages.html',
        feedbacks=feedbacks,
        volunteers=volunteers,
        email=email
    )

# 📩 Обробка запиту з форми email
@help_bp.route('/help/check_status', methods=['POST'])
def feedback_status_redirect():
    email = request.form.get('email')
    if not email:
        flash("❌ Email не вказано")
        return redirect(url_for('help.help_page'))
    return redirect(url_for('help.feedback_status', email=email))
