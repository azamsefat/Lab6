import sqlite3
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

from database import Database
from patterns import (
    AppointmentFactory,
    AppointmentObserver,
    NotificationService,
    PaymentStrategyFactory,
)


def create_app(database=None):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "replace-with-a-random-production-secret"
    app.config["DATABASE"] = database or Database()
    app.config["NOTIFIER"] = NotificationService()
    app.config["APPOINTMENT_FACTORY"] = AppointmentFactory

    db = app.config["DATABASE"]
    db.init_schema()

    @app.before_request
    def require_login():
        public_paths = (
            "/login",
            "/signup",
            "/api/health",
            "/docs",
            "/openapi.json",
            "/static/",
        )
        if request.endpoint and request.endpoint.startswith("static"):
            return None
        if request.path.startswith(public_paths):
            return None
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Authentication required"}), 401
            return redirect(url_for("login"))
        return None

    @app.get("/login")
    def login():
        if "user_id" in session:
            return redirect(url_for("index"))
        return render_template("auth.html", mode="login")

    @app.post("/login")
    def login_post():
        data = request.get_json(silent=True) or request.form
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        user = db.get_user_by_email(email)
        if not user or not check_password_hash(user["password_hash"], password):
            if request.is_json:
                return jsonify({"error": "Invalid email or password"}), 401
            return render_template(
                "auth.html", mode="login", error="Invalid email or password"
            ), 401
        session.clear()
        session.permanent = bool(data.get("remember"))
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        if request.is_json:
            return jsonify({"redirect": "/"})
        return redirect(url_for("index"))

    @app.get("/signup")
    def signup():
        if "user_id" in session:
            return redirect(url_for("index"))
        return render_template("auth.html", mode="signup")

    @app.post("/signup")
    def signup_post():
        data = request.get_json(silent=True) or request.form
        name = str(data.get("name", "")).strip()
        email = str(data.get("email", "")).strip().lower()
        password = str(data.get("password", ""))
        if not name or not email or len(password) < 8:
            message = "Name is required and password must be at least 8 characters"
            if request.is_json:
                return jsonify({"error": message}), 400
            return render_template("auth.html", mode="signup", error=message), 400
        if db.get_user_by_email(email):
            message = "An account with this email already exists"
            if request.is_json:
                return jsonify({"error": message}), 409
            return render_template("auth.html", mode="signup", error=message), 409
        try:
            user = db.create_user(name, email, generate_password_hash(password))
        except sqlite3.IntegrityError:
            message = "An account with this email already exists"
            if request.is_json:
                return jsonify({"error": message}), 409
            return render_template("auth.html", mode="signup", error=message), 409
        session.clear()
        session.permanent = bool(data.get("remember"))
        session["user_id"] = user["id"]
        session["user_name"] = user["name"]
        session["user_email"] = user["email"]
        session["user_role"] = user["role"]
        if request.is_json:
            return jsonify({"redirect": "/", "user": user}), 201
        return redirect(url_for("index"))

    @app.post("/logout")
    def logout():
        session.clear()
        if request.is_json:
            return jsonify({"redirect": "/login"})
        return redirect(url_for("login"))

    @app.get("/api/session")
    def current_session():
        return jsonify({
            "name": session["user_name"],
            "email": session["user_email"],
            "role": session["user_role"],
        })

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/dashboard")
    def dashboard():
        return jsonify(db.dashboard())

    @app.get("/api/overview")
    def overview():
        return jsonify(db.overview())

    @app.get("/api/notifications")
    def list_notifications():
        return jsonify(app.config["NOTIFIER"].list_events())

    @app.post("/api/notifications/clear")
    def clear_notifications():
        app.config["NOTIFIER"].clear()
        return jsonify({"cleared": True})

    # Patient module
    @app.get("/api/patients")
    def list_patients():
        return jsonify(db.list_patients())

    @app.post("/api/patients")
    def create_patient():
        data = request.get_json(silent=True) or {}
        required = ("name", "phone", "email")
        if any(not str(data.get(field, "")).strip() for field in required):
            return jsonify({"error": "Name, phone, and email are required"}), 400
        return jsonify(db.create_patient(data["name"], data["phone"], data["email"])), 201

    @app.put("/api/patients/<int:patient_id>")
    def update_patient(patient_id):
        data = request.get_json(silent=True) or {}
        required = ("name", "phone", "email")
        if any(not str(data.get(field, "")).strip() for field in required):
            return jsonify({"error": "Name, phone, and email are required"}), 400
        updated = db.update_patient(patient_id, data["name"], data["phone"], data["email"])
        if not updated:
            return jsonify({"error": "Patient not found"}), 404
        return jsonify(updated)

    # Doctor module
    @app.get("/api/doctors")
    def list_doctors():
        return jsonify(db.list_doctors())

    @app.post("/api/doctors")
    def create_doctor():
        data = request.get_json(silent=True) or {}
        if not str(data.get("name", "")).strip() or not str(data.get("specialty", "")).strip():
            return jsonify({"error": "Name and specialty are required"}), 400
        return jsonify(db.create_doctor(
            data["name"], data["specialty"], data.get("schedule") or "Mon-Fri, 9:00 AM-5:00 PM"
        )), 201

    @app.put("/api/doctors/<int:doctor_id>")
    def update_doctor(doctor_id):
        data = request.get_json(silent=True) or {}
        if not str(data.get("name", "")).strip() or not str(data.get("specialty", "")).strip():
            return jsonify({"error": "Name and specialty are required"}), 400
        updated = db.update_doctor(
            doctor_id,
            data["name"],
            data["specialty"],
            data.get("schedule") or "Mon-Fri, 9:00 AM-5:00 PM",
        )
        if not updated:
            return jsonify({"error": "Doctor not found"}), 404
        return jsonify(updated)

    # Appointment module
    @app.get("/api/appointments")
    def list_appointments():
        return jsonify(db.list_appointments())

    @app.post("/api/appointments")
    def create_appointment():
        data = request.get_json(silent=True) or {}
        required = ("patient_id", "doctor_id", "appointment_date", "appointment_time")
        if any(data.get(field) in (None, "") for field in required):
            return jsonify({"error": "Patient, doctor, date, and time are required"}), 400
        try:
            patient_id = int(data["patient_id"])
            doctor_id = int(data["doctor_id"])
        except (TypeError, ValueError):
            return jsonify({"error": "Valid patient and doctor IDs are required"}), 400

        if db.has_appointment_conflict(
            doctor_id, data["appointment_date"], data["appointment_time"]
        ):
            return jsonify({"error": "This doctor already has an appointment at that time"}), 409

        try:
            appointment = db.create_appointment(
                patient_id,
                doctor_id,
                data["appointment_date"],
                data["appointment_time"],
                data.get("reason", ""),
            )
        except sqlite3.IntegrityError:
            return jsonify({"error": "Selected patient or doctor was not found"}), 404
        appointment = AppointmentFactory.create("standard", appointment)
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Appointment #{appointment['id']} scheduled for "
                f"{appointment['appointment_date']} at {appointment['appointment_time']}",
                category="appointment",
            )
        )
        return jsonify(appointment), 201

    @app.post("/api/appointments/<int:appointment_id>/cancel")
    def cancel_appointment(appointment_id):
        updated = db.cancel_appointment(appointment_id)
        if not updated:
            return jsonify({"error": "Appointment not found"}), 404
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Appointment #{appointment_id} was cancelled",
                category="warning",
            )
        )
        return jsonify(updated)

    @app.post("/api/appointments/<int:appointment_id>/reschedule")
    def reschedule_appointment(appointment_id):
        data = request.get_json(silent=True) or {}
        date = data.get("appointment_date")
        time = data.get("appointment_time")
        if not date or not time:
            return jsonify({"error": "New date and time are required"}), 400
        try:
            updated = db.reschedule_appointment(appointment_id, date, time)
        except ValueError as error:
            return jsonify({"error": str(error)}), 409
        if not updated:
            return jsonify({"error": "Appointment not found"}), 404
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Appointment #{appointment_id} rescheduled to {date} at {time}",
                category="appointment",
            )
        )
        return jsonify(updated)

    # Visit module
    @app.get("/api/visits")
    def list_visits():
        return jsonify(db.list_visits())

    @app.post("/api/visits")
    def create_visit():
        data = request.get_json(silent=True) or {}
        if not data.get("appointment_id"):
            return jsonify({"error": "Appointment is required"}), 400
        try:
            appointment_id = int(data["appointment_id"])
            visit = db.create_visit(
                appointment_id,
                data.get("diagnosis", ""),
                data.get("prescription", ""),
                data.get("notes", ""),
            )
        except LookupError as error:
            return jsonify({"error": str(error)}), 409
        except ValueError as error:
            return jsonify({"error": str(error)}), 404
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Clinical visit #{visit['id']} recorded for appointment #{appointment_id}",
                category="clinical",
            )
        )
        return jsonify(visit), 201

    @app.get("/api/prescriptions")
    def list_prescriptions():
        return jsonify(db.list_prescriptions())

    @app.post("/api/prescriptions")
    def create_prescription():
        data = request.get_json(silent=True) or {}
        required = ("visit_id", "medicine", "dosage", "duration")
        if any(str(data.get(field, "")).strip() == "" for field in required):
            return jsonify({"error": "Visit, medicine, dosage, and duration are required"}), 400
        try:
            prescription = db.create_prescription(
                int(data["visit_id"]),
                data["medicine"],
                data["dosage"],
                data["duration"],
                data.get("instructions", ""),
            )
        except ValueError as error:
            return jsonify({"error": str(error)}), 404
        return jsonify(prescription), 201

    # Billing module
    @app.get("/api/bills")
    def list_bills():
        return jsonify(db.list_bills())

    @app.post("/api/bills")
    def create_bill():
        data = request.get_json(silent=True) or {}
        if not data.get("visit_id") or data.get("amount") in (None, ""):
            return jsonify({"error": "Visit and amount are required"}), 400
        try:
            bill = db.create_bill(int(data["visit_id"]), float(data["amount"]))
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Invoice #{bill['id']} created for ${float(bill['amount']):.2f}",
                category="billing",
            )
        )
        return jsonify(bill), 201

    @app.post("/api/bills/<int:bill_id>/pay")
    def pay_bill(bill_id):
        data = request.get_json(silent=True) or {}
        method = data.get("payment_method", "cash")
        try:
            payment = PaymentStrategyFactory.create(method)
        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        updated = db.pay_bill(bill_id, payment.pay(0)["payment_method"])
        if not updated:
            return jsonify({"error": "Bill not found"}), 404
        app.config["NOTIFIER"].notify(
            AppointmentObserver(
                f"Invoice #{bill_id} paid via {updated['payment_method']}",
                category="billing",
            )
        )
        return jsonify(updated)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "time": datetime.now().isoformat()})

    @app.get("/docs")
    def api_docs():
        return render_template("swagger.html")

    @app.get("/openapi.json")
    def openapi():
        return jsonify({
            "openapi": "3.0.3",
            "info": {
                "title": "Medicare Clinic API",
                "version": "1.0.0",
                "description": "Clinic appointment, patient, visit, prescription, and billing API.",
            },
            "servers": [{"url": "/"}],
            "paths": {
                "/api/dashboard": {
                    "get": {"summary": "Dashboard entity counts", "responses": {"200": {"description": "Counts"}}},
                },
                "/api/overview": {
                    "get": {"summary": "Detailed clinic overview metrics", "responses": {"200": {"description": "Overview"}}},
                },
                "/api/notifications": {
                    "get": {"summary": "Recent system notifications", "responses": {"200": {"description": "Notifications"}}},
                },
                "/api/patients": {
                    "get": {"summary": "List patients", "responses": {"200": {"description": "Patient list"}}},
                    "post": {"summary": "Register patient", "responses": {"201": {"description": "Patient created"}}},
                },
                "/api/patients/{patient_id}": {
                    "put": {"summary": "Update patient", "responses": {"200": {"description": "Patient updated"}}},
                },
                "/api/doctors": {
                    "get": {"summary": "List doctors", "responses": {"200": {"description": "Doctor list"}}},
                    "post": {"summary": "Register doctor", "responses": {"201": {"description": "Doctor created"}}},
                },
                "/api/doctors/{doctor_id}": {
                    "put": {"summary": "Update doctor", "responses": {"200": {"description": "Doctor updated"}}},
                },
                "/api/appointments": {
                    "get": {"summary": "List appointments", "responses": {"200": {"description": "Appointment list"}}},
                    "post": {"summary": "Schedule appointment", "responses": {"201": {"description": "Appointment scheduled"}}},
                },
                "/api/appointments/{appointment_id}/reschedule": {
                    "post": {"summary": "Reschedule appointment", "responses": {"200": {"description": "Appointment rescheduled"}}},
                },
                "/api/appointments/{appointment_id}/cancel": {
                    "post": {"summary": "Cancel appointment", "responses": {"200": {"description": "Appointment cancelled"}}},
                },
                "/api/visits": {
                    "get": {"summary": "List visits", "responses": {"200": {"description": "Visit list"}}},
                    "post": {"summary": "Record visit", "responses": {"201": {"description": "Visit recorded"}}},
                },
                "/api/prescriptions": {
                    "get": {"summary": "List prescriptions", "responses": {"200": {"description": "Prescription list"}}},
                    "post": {"summary": "Create prescription", "responses": {"201": {"description": "Prescription created"}}},
                },
                "/api/bills": {
                    "get": {"summary": "List bills", "responses": {"200": {"description": "Bill list"}}},
                    "post": {"summary": "Create bill", "responses": {"201": {"description": "Bill created"}}},
                },
                "/api/bills/{bill_id}/pay": {
                    "post": {"summary": "Pay bill", "responses": {"200": {"description": "Bill paid"}}},
                },
            },
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
