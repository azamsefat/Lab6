from database import Database


def test_database_is_singleton(database):
    assert Database() is database


def test_bill_rejects_non_positive_amount(database):
    database.create_patient("Test", "123", "test@example.com")
    database.create_doctor("Doctor", "General")
    appointment = database.create_appointment(1, 1, "2026-12-01", "09:00", "Checkup")
    visit = database.create_visit(appointment["id"], "None", "None", "")
    try:
        database.create_bill(visit["id"], 0)
        assert False, "Expected ValueError"
    except ValueError as error:
        assert "greater than zero" in str(error)
