from unittest.mock import Mock


def test_health_endpoint(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json["status"] == "ok"


def test_create_and_list_patient(client):
    response = client.post(
        "/api/patients",
        json={"name": "Amina Rahman", "phone": "01700000000", "email": "amina@example.com"},
    )
    assert response.status_code == 201
    assert response.json["name"] == "Amina Rahman"
    assert client.get("/api/patients").json[0]["email"] == "amina@example.com"


def test_patient_validation(client):
    response = client.post("/api/patients", json={"name": "", "phone": "", "email": ""})
    assert response.status_code == 400


def test_create_doctor_and_appointment(client):
    patient = client.post(
        "/api/patients",
        json={"name": "Patient", "phone": "123", "email": "p@example.com"},
    ).json
    doctor = client.post(
        "/api/doctors", json={"name": "Dr. Karim", "specialty": "Cardiology"}
    ).json
    response = client.post(
        "/api/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "appointment_date": "2026-12-01",
            "appointment_time": "10:30",
            "reason": "Chest pain",
        },
    )
    assert response.status_code == 201
    assert response.json["appointment_type"] == "Standard consultation"


def test_prevents_duplicate_appointment(client):
    patient = client.post(
        "/api/patients",
        json={"name": "Patient", "phone": "123", "email": "p@example.com"},
    ).json
    doctor = client.post(
        "/api/doctors", json={"name": "Dr. Karim", "specialty": "Cardiology"}
    ).json
    payload = {
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_date": "2026-12-01",
        "appointment_time": "10:30",
    }
    assert client.post("/api/appointments", json=payload).status_code == 201
    assert client.post("/api/appointments", json=payload).status_code == 409


def test_visit_and_bill_workflow(client):
    patient = client.post(
        "/api/patients",
        json={"name": "Patient", "phone": "123", "email": "p@example.com"},
    ).json
    doctor = client.post(
        "/api/doctors", json={"name": "Dr. Karim", "specialty": "Cardiology"}
    ).json
    appointment = client.post(
        "/api/appointments",
        json={
            "patient_id": patient["id"],
            "doctor_id": doctor["id"],
            "appointment_date": "2026-12-01",
            "appointment_time": "10:30",
        },
    ).json
    visit = client.post(
        "/api/visits",
        json={"appointment_id": appointment["id"], "diagnosis": "Healthy", "prescription": "Rest"},
    )
    assert visit.status_code == 201
    bill = client.post(
        "/api/bills", json={"visit_id": visit.json["id"], "amount": 750}
    )
    assert bill.status_code == 201
    assert client.post(f"/api/bills/{bill.json['id']}/pay").json["status"] == "paid"


def test_external_notifier_is_mocked(database):
    notifier = Mock()
    notifier.notify = Mock()
    observer = Mock()
    notifier.notify(observer)
    notifier.notify.assert_called_once_with(observer)


def test_login_required(database):
    from app import create_app

    app = create_app(database)
    app.config.update(TESTING=True)
    guest = app.test_client()
    assert guest.get("/").status_code == 302
    assert guest.get("/api/patients").status_code == 401


def test_signup_and_login(database):
    from app import create_app

    app = create_app(database)
    app.config.update(TESTING=True)
    visitor = app.test_client()
    signup = visitor.post(
        "/signup",
        json={"name": "Clinic Admin", "email": "clinic@example.com", "password": "secure123"},
    )
    assert signup.status_code == 201
    assert visitor.get("/api/session").status_code == 200
    visitor.post("/logout", json={})
    login = visitor.post(
        "/login",
        json={"email": "clinic@example.com", "password": "secure123"},
    )
    assert login.status_code == 200


def test_reschedule_appointment(client):
    patient = client.post("/api/patients", json={
        "name": "Patient", "phone": "123", "email": "patient@example.com"
    }).json
    doctor = client.post("/api/doctors", json={
        "name": "Dr. Test", "specialty": "General", "schedule": "Mon-Fri"
    }).json
    appointment = client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_date": "2026-12-10",
        "appointment_time": "10:00",
    }).json
    response = client.post(
        f"/api/appointments/{appointment['id']}/reschedule",
        json={"appointment_date": "2026-12-11", "appointment_time": "11:00"},
    )
    assert response.status_code == 200
    assert response.json["appointment_date"] == "2026-12-11"


def test_prescription_and_payment_strategies(client):
    patient = client.post("/api/patients", json={
        "name": "Patient", "phone": "123", "email": "rx@example.com"
    }).json
    doctor = client.post("/api/doctors", json={
        "name": "Dr. Test", "specialty": "General"
    }).json
    appointment = client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_date": "2026-12-12",
        "appointment_time": "09:00",
    }).json
    visit = client.post("/api/visits", json={
        "appointment_id": appointment["id"], "diagnosis": "Flu"
    }).json
    prescription = client.post("/api/prescriptions", json={
        "visit_id": visit["id"],
        "medicine": "Paracetamol",
        "dosage": "500mg",
        "duration": "5 days",
    })
    assert prescription.status_code == 201
    bill = client.post("/api/bills", json={"visit_id": visit["id"], "amount": 500}).json
    payment = client.post(
        f"/api/bills/{bill['id']}/pay",
        json={"payment_method": "bkash"},
    )
    assert payment.status_code == 200
    assert payment.json["payment_method"] == "bKash"


def test_update_patient_doctor_overview_and_notifications(client):
    patient = client.post("/api/patients", json={
        "name": "Old Name", "phone": "111", "email": "old@example.com"
    }).json
    updated_p = client.put(f"/api/patients/{patient['id']}", json={
        "name": "New Name", "phone": "222", "email": "new@example.com"
    })
    assert updated_p.status_code == 200
    assert updated_p.json["name"] == "New Name"

    doctor = client.post("/api/doctors", json={
        "name": "Dr. Old", "specialty": "General"
    }).json
    updated_d = client.put(f"/api/doctors/{doctor['id']}", json={
        "name": "Dr. New", "specialty": "Cardiology", "schedule": "Mon-Thu"
    })
    assert updated_d.status_code == 200
    assert updated_d.json["specialty"] == "Cardiology"

    appt = client.post("/api/appointments", json={
        "patient_id": patient["id"],
        "doctor_id": doctor["id"],
        "appointment_date": "2026-12-15",
        "appointment_time": "14:00",
        "reason": "Checkup",
    }).json
    visit = client.post("/api/visits", json={"appointment_id": appt["id"], "diagnosis": "OK"})
    assert visit.status_code == 201
    dup_visit = client.post("/api/visits", json={"appointment_id": appt["id"], "diagnosis": "Dup"})
    assert dup_visit.status_code == 409

    bill = client.post("/api/bills", json={"visit_id": visit.json["id"], "amount": 300}).json
    client.post(f"/api/bills/{bill['id']}/pay", json={"payment_method": "card"})

    overview = client.get("/api/overview")
    assert overview.status_code == 200
    assert overview.json["paid_revenue"] == 300.0
    assert overview.json["scheduled_appointments"] == 1

    notifs = client.get("/api/notifications")
    assert notifs.status_code == 200
    assert len(notifs.json) >= 2
    assert client.post("/api/notifications/clear").status_code == 200
    assert client.get("/api/notifications").json == []


def test_invalid_appointment_ids_return_400(client):
    resp = client.post("/api/appointments", json={
        "patient_id": "abc",
        "doctor_id": 1,
        "appointment_date": "2026-12-20",
        "appointment_time": "09:00",
    })
    assert resp.status_code == 400
