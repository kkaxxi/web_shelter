from flask import render_template
from flask_login import current_user
from models import MonthlyReport
from . import reports_bp  # ← ІМПОРТ, а не створення

@reports_bp.route('/reports')
def reports_page():
    reports = MonthlyReport.query.order_by(MonthlyReport.year.desc(), MonthlyReport.month_number).all()
    years = sorted(set(r.year for r in reports), reverse=True)
    return render_template('reports.html', reports=reports, years=years)
