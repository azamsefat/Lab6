import sqlite3
import threading
from pathlib import Path


class Database:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, path="clinic.db"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.path = str(path)
            return cls._instance

    @classmethod
    def reset(cls):
        cls._instance = None

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def init_schema(self):
        with self.connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    email TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS doctors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    specialty TEXT NOT NULL,
                    schedule TEXT NOT NULL DEFAULT 'Mon-Fri, 9:00 AM-5:00 PM'
                );
                CREATE TABLE IF NOT EXISTS appointments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patient_id INTEGER NOT NULL,
                    doctor_id INTEGER NOT NULL,
                    appointment_date TEXT NOT NULL,
                    appointment_time TEXT NOT NULL,
                    reason TEXT,
                    status TEXT NOT NULL DEFAULT 'scheduled',
                    FOREIGN KEY(patient_id) REFERENCES patients(id),
                    FOREIGN KEY(doctor_id) REFERENCES doctors(id)
                );
                CREATE TABLE IF NOT EXISTS visits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL UNIQUE,
                    diagnosis TEXT,
                    prescription TEXT,
                    notes TEXT,
                    FOREIGN KEY(appointment_id) REFERENCES appointments(id)
                );
                CREATE TABLE IF NOT EXISTS bills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visit_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    payment_method TEXT,
                    FOREIGN KEY(visit_id) REFERENCES visits(id)
                );
                CREATE TABLE IF NOT EXISTS prescriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    visit_id INTEGER NOT NULL,
                    medicine TEXT NOT NULL,
                    dosage TEXT NOT NULL,
                    duration TEXT NOT NULL,
                    instructions TEXT,
                    FOREIGN KEY(visit_id) REFERENCES visits(id)
                );
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL DEFAULT 'staff',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            for table, column, definition in (
                ("doctors", "schedule", "TEXT NOT NULL DEFAULT 'Mon-Fri, 9:00 AM-5:00 PM'"),
                ("bills", "payment_method", "TEXT"),
            ):
                columns = {row["name"] for row in connection.execute(f"PRAGMA table_info({table})")}
                if column not in columns:
                    connection.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")

    @staticmethod
    def _rows(connection, query, parameters=()):
        return [dict(row) for row in connection.execute(query, parameters).fetchall()]

    def list_patients(self):
        with self.connect() as connection:
            return self._rows(connection, "SELECT * FROM patients ORDER BY id DESC")

    def create_patient(self, name, phone, email):
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO patients(name, phone, email) VALUES (?, ?, ?)",
                (name.strip(), phone.strip(), email.strip()),
            )
            return self._rows(connection, "SELECT * FROM patients WHERE id = ?", (cursor.lastrowid,))[0]

    def update_patient(self, patient_id, name, phone, email):
        with self.connect() as connection:
            connection.execute(
                "UPDATE patients SET name = ?, phone = ?, email = ? WHERE id = ?",
                (name.strip(), phone.strip(), email.strip(), patient_id),
            )
            rows = self._rows(connection, "SELECT * FROM patients WHERE id = ?", (patient_id,))
            return rows[0] if rows else None

    def list_doctors(self):
        with self.connect() as connection:
            return self._rows(connection, "SELECT * FROM doctors ORDER BY id DESC")

    def create_doctor(self, name, specialty, schedule="Mon-Fri, 9:00 AM-5:00 PM"):
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO doctors(name, specialty, schedule) VALUES (?, ?, ?)",
                (name.strip(), specialty.strip(), schedule.strip()),
            )
            return self._rows(connection, "SELECT * FROM doctors WHERE id = ?", (cursor.lastrowid,))[0]

    def update_doctor(self, doctor_id, name, specialty, schedule):
        with self.connect() as connection:
            connection.execute(
                "UPDATE doctors SET name = ?, specialty = ?, schedule = ? WHERE id = ?",
                (name.strip(), specialty.strip(), schedule.strip(), doctor_id),
            )
            rows = self._rows(connection, "SELECT * FROM doctors WHERE id = ?", (doctor_id,))
            return rows[0] if rows else None

    def has_appointment_conflict(self, doctor_id, date, time):
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT COUNT(*) AS count FROM appointments
                WHERE doctor_id = ? AND appointment_date = ? AND appointment_time = ?
                AND status != 'cancelled'
                """,
                (doctor_id, date, time),
            ).fetchone()
            return row["count"] > 0

    def list_appointments(self):
        with self.connect() as connection:
            return self._rows(
                connection,
                """
                SELECT a.*, p.name AS patient_name, d.name AS doctor_name,
                       d.specialty AS doctor_specialty,
                       CASE WHEN v.id IS NOT NULL THEN 1 ELSE 0 END AS has_visit,
                       v.id AS visit_id
                FROM appointments a
                JOIN patients p ON p.id = a.patient_id
                JOIN doctors d ON d.id = a.doctor_id
                LEFT JOIN visits v ON v.appointment_id = a.id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
                """,
            )

    def create_appointment(self, patient_id, doctor_id, date, time, reason):
        with self.connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO appointments(patient_id, doctor_id, appointment_date,
                                         appointment_time, reason)
                VALUES (?, ?, ?, ?, ?)
                """,
                (patient_id, doctor_id, date, time, reason.strip()),
            )
            row = connection.execute(
                "SELECT * FROM appointments WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)

    def cancel_appointment(self, appointment_id):
        with self.connect() as connection:
            connection.execute(
                "UPDATE appointments SET status = 'cancelled' WHERE id = ?", (appointment_id,)
            )
            row = connection.execute(
                "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            return dict(row) if row else None

    def reschedule_appointment(self, appointment_id, date, time):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT doctor_id, status FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if not row:
                return None
            if row["status"] == "cancelled":
                raise ValueError("Cancelled appointments cannot be rescheduled")
            conflict = connection.execute(
                """
                SELECT COUNT(*) AS count FROM appointments
                WHERE id != ? AND doctor_id = ? AND appointment_date = ?
                AND appointment_time = ? AND status != 'cancelled'
                """,
                (appointment_id, row["doctor_id"], date, time),
            ).fetchone()
            if conflict["count"] > 0:
                raise ValueError("This doctor already has an appointment at that time")
            connection.execute(
                "UPDATE appointments SET appointment_date = ?, appointment_time = ? WHERE id = ?",
                (date, time, appointment_id),
            )
            updated = connection.execute(
                "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            return dict(updated)

    def list_visits(self):
        with self.connect() as connection:
            return self._rows(
                connection,
                """
                SELECT v.*, a.patient_id, a.doctor_id, a.appointment_date,
                       a.appointment_time, a.reason,
                       p.name AS patient_name, d.name AS doctor_name,
                       d.specialty AS doctor_specialty
                FROM visits v
                JOIN appointments a ON a.id = v.appointment_id
                JOIN patients p ON p.id = a.patient_id
                JOIN doctors d ON d.id = a.doctor_id
                ORDER BY v.id DESC
                """,
            )

    def create_visit(self, appointment_id, diagnosis, prescription, notes):
        with self.connect() as connection:
            appointment = connection.execute(
                "SELECT id, status FROM appointments WHERE id = ?", (appointment_id,)
            ).fetchone()
            if not appointment:
                raise ValueError("Appointment not found")
            if appointment["status"] == "cancelled":
                raise ValueError("Cannot record a visit for a cancelled appointment")
            existing = connection.execute(
                "SELECT id FROM visits WHERE appointment_id = ?", (appointment_id,)
            ).fetchone()
            if existing:
                raise LookupError("A clinical visit has already been recorded for this appointment")
            cursor = connection.execute(
                """
                INSERT INTO visits(appointment_id, diagnosis, prescription, notes)
                VALUES (?, ?, ?, ?)
                """,
                (appointment_id, diagnosis.strip(), prescription.strip(), notes.strip()),
            )
            row = connection.execute("SELECT * FROM visits WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return dict(row)

    def create_prescription(self, visit_id, medicine, dosage, duration, instructions=""):
        with self.connect() as connection:
            visit = connection.execute("SELECT id FROM visits WHERE id = ?", (visit_id,)).fetchone()
            if not visit:
                raise ValueError("Visit not found")
            cursor = connection.execute(
                """
                INSERT INTO prescriptions(visit_id, medicine, dosage, duration, instructions)
                VALUES (?, ?, ?, ?, ?)
                """,
                (visit_id, medicine.strip(), dosage.strip(), duration.strip(), instructions.strip()),
            )
            row = connection.execute(
                "SELECT * FROM prescriptions WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)

    def list_prescriptions(self):
        with self.connect() as connection:
            return self._rows(
                connection,
                """
                SELECT pr.*, v.appointment_id, v.diagnosis,
                       a.appointment_date, p.name AS patient_name,
                       d.name AS doctor_name
                FROM prescriptions pr
                JOIN visits v ON v.id = pr.visit_id
                JOIN appointments a ON a.id = v.appointment_id
                JOIN patients p ON p.id = a.patient_id
                JOIN doctors d ON d.id = a.doctor_id
                ORDER BY pr.id DESC
                """,
            )

    def list_bills(self):
        with self.connect() as connection:
            return self._rows(
                connection,
                """
                SELECT b.*, v.appointment_id, v.diagnosis,
                       a.appointment_date, p.name AS patient_name,
                       d.name AS doctor_name
                FROM bills b
                JOIN visits v ON v.id = b.visit_id
                JOIN appointments a ON a.id = v.appointment_id
                JOIN patients p ON p.id = a.patient_id
                JOIN doctors d ON d.id = a.doctor_id
                ORDER BY b.id DESC
                """,
            )

    def create_bill(self, visit_id, amount):
        if amount <= 0:
            raise ValueError("Amount must be greater than zero")
        with self.connect() as connection:
            visit = connection.execute("SELECT id FROM visits WHERE id = ?", (visit_id,)).fetchone()
            if not visit:
                raise ValueError("Visit not found")
            cursor = connection.execute(
                "INSERT INTO bills(visit_id, amount) VALUES (?, ?)", (visit_id, amount)
            )
            row = connection.execute("SELECT * FROM bills WHERE id = ?", (cursor.lastrowid,)).fetchone()
            return dict(row)

    def pay_bill(self, bill_id, payment_method="cash"):
        with self.connect() as connection:
            connection.execute(
                "UPDATE bills SET status = 'paid', payment_method = ? WHERE id = ?",
                (payment_method, bill_id),
            )
            row = connection.execute("SELECT * FROM bills WHERE id = ?", (bill_id,)).fetchone()
            return dict(row) if row else None

    def dashboard(self):
        with self.connect() as connection:
            def count(table):
                return connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

            return {
                "patients": count("patients"),
                "doctors": count("doctors"),
                "appointments": count("appointments"),
                "visits": count("visits"),
                "bills": count("bills"),
            }

    def overview(self):
        with self.connect() as connection:
            counts = self.dashboard()
            scheduled_count = connection.execute(
                "SELECT COUNT(*) FROM appointments WHERE status = 'scheduled'"
            ).fetchone()[0]
            cancelled_count = connection.execute(
                "SELECT COUNT(*) FROM appointments WHERE status = 'cancelled'"
            ).fetchone()[0]
            paid_revenue = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM bills WHERE status = 'paid'"
            ).fetchone()[0]
            pending_revenue = connection.execute(
                "SELECT COALESCE(SUM(amount), 0) FROM bills WHERE status = 'pending'"
            ).fetchone()[0]
            pending_bills = connection.execute(
                "SELECT COUNT(*) FROM bills WHERE status = 'pending'"
            ).fetchone()[0]
            prescription_count = connection.execute(
                "SELECT COUNT(*) FROM prescriptions"
            ).fetchone()[0]
            payment_breakdown = self._rows(
                connection,
                """
                SELECT COALESCE(payment_method, 'cash') AS method,
                       COUNT(*) AS count,
                       COALESCE(SUM(amount), 0) AS total
                FROM bills
                WHERE status = 'paid'
                GROUP BY COALESCE(payment_method, 'cash')
                """,
            )
            return {
                "counts": counts,
                "scheduled_appointments": scheduled_count,
                "cancelled_appointments": cancelled_count,
                "paid_revenue": round(float(paid_revenue), 2),
                "pending_revenue": round(float(pending_revenue), 2),
                "pending_bills": pending_bills,
                "prescriptions": prescription_count,
                "payment_breakdown": payment_breakdown,
            }

    def create_user(self, name, email, password_hash, role="staff"):
        with self.connect() as connection:
            cursor = connection.execute(
                "INSERT INTO users(name, email, password_hash, role) VALUES (?, ?, ?, ?)",
                (name.strip(), email.strip().lower(), password_hash, role),
            )
            row = connection.execute(
                "SELECT id, name, email, role FROM users WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
            return dict(row)

    def get_user_by_email(self, email):
        with self.connect() as connection:
            row = connection.execute(
                "SELECT id, name, email, password_hash, role FROM users WHERE email = ?",
                (email.strip().lower(),),
            ).fetchone()
            return dict(row) if row else None
