import os
from flask import Flask
from models import db, MonthlyReport
from routes.reports import generate_report_pdf  # ⚠️ імпортуй функцію з reports.py

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))

# Конфігурація
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, '..', 'db', 'database.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['REPORTS_FOLDER'] = os.path.join(basedir, 'static', 'reports')
os.makedirs(app.config['REPORTS_FOLDER'], exist_ok=True)

db.init_app(app)

# Трансліт для генерації імені PDF
month_translit = {
    "Січень": "sichen",
    "Лютий": "liutyi"
}

data = [
    {
        "month": "Січень",
        "month_number": 1,
        "year": 2025,
        "income": 15000,
        "expenses": 13500,
        "adopted_animals": 4,
        "new_animals": 2,
        "sub": {
            "operating_costs": 3000,
            "vet_services": 2000,
            "garbage": 1000,
            "salary": 3000,
            "dry_food": 2000,
            "cat_litter": 1000,
            "grains": 1000,
            "construction": 500
        }
    },
    {
        "month": "Лютий",
        "month_number": 2,
        "year": 2025,
        "income": 18000,
        "expenses": 16200,
        "adopted_animals": 5,
        "new_animals": 3,
        "sub": {
            "operating_costs": 4000,
            "vet_services": 2000,
            "garbage": 1200,
            "salary": 3000,
            "dry_food": 2000,
            "cat_litter": 1000,
            "grains": 2000,
            "construction": 1000
        }
    }
]

with app.app_context():
    db.create_all()

    for d in data:
        filename = f"{month_translit[d['month']]}_{d['year']}.pdf"
        pdf_url = f"/static/reports/{filename}"

        report = MonthlyReport(
            year=d["year"],
            month=d["month"],
            month_number=d["month_number"],
            income=d["income"],
            expenses=d["expenses"],
            adopted_animals=d["adopted_animals"],
            new_animals=d["new_animals"],
            pdf_url=pdf_url,
            **d["sub"]
        )

        db.session.add(report)
        db.session.commit()

        # Генерація PDF
        generate_report_pdf(report, app)

    print("✅ Тестові звіти за Січень і Лютий 2025 додані!")
