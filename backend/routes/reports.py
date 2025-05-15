from flask import render_template, request, redirect, url_for, flash, abort, current_app, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
import os

from forms import MonthlyReportForm
from models import db, MonthlyReport, Donation
from datetime import datetime
from . import reports_bp

from flask_wtf import FlaskForm
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

# 📝 Dummy form for CSRF в шаблоні
class DummyForm(FlaskForm):
    pass

# 📋 Сторінка перегляду всіх звітів
@reports_bp.route('/reports')
def reports_page():
    reports = MonthlyReport.query.order_by(MonthlyReport.year.desc(), MonthlyReport.month_number).all()
    years = sorted(set(r.year for r in reports), reverse=True)
    dummy_form = DummyForm()
    return render_template('reports.html', reports=reports, years=years, form=dummy_form)

# ➕ Додавання нового звіту
@reports_bp.route('/reports/add', methods=['GET', 'POST'])
@login_required
def add_report():
    if current_user.role != 'admin':
        abort(403)

    form = MonthlyReportForm()

    # 💸 Автопідрахунок надходжень
    donation_sum = db.session.query(db.func.sum(Donation.amount))\
        .filter(db.extract('year', Donation.timestamp) == form.year.data)\
        .filter(db.extract('month', Donation.timestamp) == form.month_number.data)\
        .scalar() or 0
    form.income.data = donation_sum

    if form.validate_on_submit():
        month_translit = {
            "Січень": "sichen",
            "Лютий": "liutyi",
            "Березень": "berezen",
            "Квітень": "kviten",
            "Травень": "traven",
            "Червень": "cherven",
            "Липень": "lypen",
            "Серпень": "serpen",
            "Вересень": "veresen",
            "Жовтень": "zhovten",
            "Листопад": "lystopad",
            "Грудень": "hruden"
        }

        filename = f"{month_translit.get(form.month.data, 'misyats')}_{form.year.data}.pdf"
        pdf_url = f'/static/reports/{filename}'

        # ❗ Перевірка відповідності суми витрат
        total_sub_expenses = sum([
            form.operating_costs.data or 0,
            form.vet_services.data or 0,
            form.garbage.data or 0,
            form.salary.data or 0,
            form.dry_food.data or 0,
            form.cat_litter.data or 0,
            form.grains.data or 0,
            form.construction.data or 0
        ])
        if form.expenses.data != total_sub_expenses:
            flash("❌ Сума витрат не відповідає сумі по категоріях!")
            return render_template('add_report.html', form=form)

        # 📥 Збереження в БД
        report = MonthlyReport(
            year=form.year.data,
            month=form.month.data,
            month_number=form.month_number.data,
            income=form.income.data,
            expenses=form.expenses.data,
            operating_costs=form.operating_costs.data,
            vet_services=form.vet_services.data,
            garbage=form.garbage.data,
            salary=form.salary.data,
            dry_food=form.dry_food.data,
            cat_litter=form.cat_litter.data,
            grains=form.grains.data,
            construction=form.construction.data,
            adopted_animals=form.adopted_animals.data,
            new_animals=form.new_animals.data,
            pdf_url=pdf_url
        )
        db.session.add(report)
        db.session.commit()

        # 📄 Генерація PDF
        generate_report_pdf(report, current_app)

        flash("✅ Звіт створено та PDF згенеровано!")
        return redirect(url_for('reports.reports_page'))

    return render_template('add_report.html', form=form)

# 📄 Генерація PDF-файлу на основі звіту
def generate_report_pdf(report, app):
    filename = os.path.basename(report.pdf_url)
    filepath = os.path.join(app.config['REPORTS_FOLDER'], filename)

    # 🖋️ Шрифт з підтримкою кирилиці
    font_path = os.path.join(app.root_path, 'static', 'fonts', 'DejaVuSans.ttf')
    pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))

    c = canvas.Canvas(filepath)
    c.setFont("DejaVuSans", 14)
    y = 820
    line_height = 22

    c.drawString(100, y, f"Фінансовий звіт за {report.month} {report.year}")
    c.setFont("DejaVuSans", 12)
    y -= line_height
    c.drawString(100, y, f"Надходження: {report.income} грн")
    y -= line_height
    c.drawString(100, y, f"Загальні витрати: {report.expenses} грн")

    y -= line_height * 2
    c.drawString(100, y, "Деталізація витрат:")
    y -= line_height

    sub_expenses = {
        "Функціонування притулку": report.operating_costs,
        "Ветеринарні послуги": report.vet_services,
        "Вивіз сміття": report.garbage,
        "Заробітна плата": report.salary,
        "Сухий корм": report.dry_food,
        "Котячий наповнювач": report.cat_litter,
        "Крупи": report.grains,
        "Будівельні витрати": report.construction
    }

    for label, value in sub_expenses.items():
        c.drawString(120, y, f"{label}: {value} грн")
        y -= line_height

    y -= line_height
    c.drawString(100, y, f"🐾 Усиновлено тварин: {report.adopted_animals}")
    y -= line_height
    c.drawString(100, y, f"🐶 Нових тварин: {report.new_animals}")
    c.save()

# 📂 Відкриття PDF для перегляду/завантаження
@reports_bp.route('/reports/pdf/<filename>')
def serve_pdf(filename):
    pdf_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)
    if not os.path.exists(pdf_path):
        abort(404)
    return send_file(pdf_path, mimetype='application/pdf')

# ❌ Видалення звіту
@reports_bp.route('/reports/delete/<int:report_id>', methods=['POST'])
@login_required
def delete_report(report_id):
    if current_user.role != 'admin':
        abort(403)

    report = MonthlyReport.query.get_or_404(report_id)

    # 🗑️ Спроба видалити PDF-файл
    if report.pdf_url:
        try:
            filename = os.path.basename(report.pdf_url)
            pdf_path = os.path.join(current_app.config['REPORTS_FOLDER'], filename)
            if os.path.exists(pdf_path):
                os.remove(pdf_path)
            else:
                flash(f"⚠️ Файл не знайдено: {filename}")
        except Exception as e:
            flash(f"⚠️ Помилка при видаленні PDF: {str(e)}")

    db.session.delete(report)
    db.session.commit()
    flash("✅ Звіт видалено!")
    return redirect(url_for('reports.reports_page'))
