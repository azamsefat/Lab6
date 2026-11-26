from werkzeug.security import generate_password_hash

from app import app


def seed():
    db = app.config["DATABASE"]
    db.init_schema()
    if not db.get_user_by_email("admin@medicare.local"):
        db.create_user(
            "Administrator",
            "admin@medicare.local",
            generate_password_hash("admin123"),
            "Administrator",
        )
    if db.list_patients():
        return
    p1 = db.create_patient("Amina Rahman", "01700-000001", "amina@example.com")
    p2 = db.create_patient("Tanvir Ahmed", "01711-234567", "tanvir@example.com")
    p3 = db.create_patient("Nusrat Jahan", "01819-876543", "nusrat@example.com")

    d1 = db.create_doctor("Dr. Shahriar Karim", "Cardiology", "Sun-Thu, 9:00 AM-4:00 PM")
    d2 = db.create_doctor("Dr. Farhana Yasmin", "Pediatrics", "Mon-Fri, 10:00 AM-6:00 PM")
    d3 = db.create_doctor("Dr. Mahbub Alam", "Internal Medicine", "Sat-Wed, 8:30 AM-2:30 PM")

    a1 = db.create_appointment(
        p1["id"], d1["id"], "2026-12-01", "10:30", "Routine heart checkup"
    )
    a2 = db.create_appointment(
        p2["id"], d2["id"], "2026-12-02", "11:15", "Seasonal fever & cough"
    )
    db.create_appointment(
        p3["id"], d3["id"], "2026-12-03", "09:45", "Annual wellness screening"
    )

    v1 = db.create_visit(
        a1["id"],
        "Normal sinus rhythm, mild fatigue",
        "Vitamin D3 + Balanced diet",
        "Follow up in 3 months with ECG",
    )
    v2 = db.create_visit(
        a2["id"],
        "Acute viral upper respiratory infection",
        "Antipyretic & hydration",
        "Rest for 3 days, return if fever persists",
    )

    db.create_prescription(
        v1["id"], "Cholecalciferol (Vitamin D3)", "1000 IU", "30 days", "Take once daily after lunch"
    )
    db.create_prescription(
        v2["id"], "Paracetamol", "500mg", "5 days", "Take 1 tablet every 8 hours if fever > 100°F"
    )

    b1 = db.create_bill(v1["id"], 1200)
    db.pay_bill(b1["id"], "bKash")
    db.create_bill(v2["id"], 850)


if __name__ == "__main__":
    seed()
    print("Sample data added.")
