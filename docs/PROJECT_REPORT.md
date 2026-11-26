# CSE 3206 Project Report

## 1. Problem statement and scope

The project is a clinic appointment system that manages patient registration, doctor records, appointments, clinical visits, and billing. It replaces separate paper or spreadsheet workflows with one persistent application and prevents duplicate booking of a doctor at the same date and time.

## 2. Requirements

### Functional requirements

| ID | Requirement |
|---|---|
| FR-01 | The receptionist can register a patient with name, phone, and email. |
| FR-02 | The receptionist can register a doctor with name and specialty. |
| FR-03 | The receptionist can schedule an appointment for a patient and doctor. |
| FR-04 | The system rejects an appointment when the selected doctor is already scheduled at that date and time. |
| FR-05 | The receptionist can cancel a scheduled appointment. |
| FR-06 | The clinician can record diagnosis, prescription, and notes for an appointment. |
| FR-07 | The billing user can create a positive-amount bill for a visit. |
| FR-08 | The billing user can mark a bill paid. |
| FR-09 | The dashboard summarizes entity counts. |
| FR-10 | The receptionist can reschedule an appointment and the system prevents the new time conflict. |
| FR-11 | The clinician can issue a separate prescription linked to a visit. |
| FR-12 | Billing can process Cash, Card, or bKash payment strategies. |
| FR-13 | Staff can sign up, log in, and log out through authenticated sessions. |

### Non-functional requirements

| ID | Requirement |
|---|---|
| NFR-01 | Records persist in SQLite across restarts. |
| NFR-02 | Invalid requests return HTTP 400 or 404 where appropriate. |
| NFR-03 | Appointment conflicts return HTTP 409. |
| NFR-04 | The interface supports desktop and mobile widths. |
| NFR-05 | Automated tests cover scheduling, validation, persistence, and browser rendering. |

## 3. Use cases

**Schedule appointment:** Receptionist opens Appointments, selects patient and doctor, enters date/time and reason, and submits. The system validates required fields and checks conflicts. A standard appointment is created and a notification event is emitted.

**Record visit:** Clinician selects an appointment and enters diagnosis, prescription, and notes. The system stores one visit record and makes it available for billing.

**Create and pay bill:** Billing staff selects a visit, enters a positive amount, and creates a bill. Staff later marks it paid.

## 4. Process model

Incremental development was selected. Each increment delivered one workflow and test layer, allowing requirements to be checked before extending the system. Agile would offer faster feedback, but this small local project had stable educational deliverables and benefited from the disciplined evidence between increments.

## 5. Prototype

The responsive UI in `templates/index.html` and `static/styles.css` acts as the implemented mock-up. Navigation separates the five modules, and cards/forms provide a simple information hierarchy.

## 6. Design pattern analysis

- **Singleton (`Database`) -- problem:** consistent SQLite path and schema. **Rejected alternative:** creating a database object in each route, because it would duplicate lifecycle and singleton state.
- **Factory Method (`AppointmentFactory`) -- problem:** separate appointment representations and avoid route-specific construction rules. **Rejected alternative:** constructors directly in routes, because type rules would be duplicated.
- **Observer (`NotificationService`/`AppointmentObserver`) -- problem:** decouple notification events from scheduling and payment. **Rejected alternative:** direct print calls in database methods, because it would mix persistence with presentation/notification concerns.
- **Strategy (`PaymentStrategyFactory`) -- problem:** choose Cash, Card, or bKash payment behavior without route-specific logic. **Rejected alternative:** one `if/else` method, because new payment methods would require modifying and retesting that method.
- **Factory (`ClinicUserFactory`) -- problem:** validate and construct supported Patient, Doctor, Receptionist, and Admin role profiles. **Rejected alternative:** direct role dictionaries in authentication code, because role rules would be duplicated.

## 7. Software testing

TDD was applied to validation and appointment workflow tests before implementation was expanded. pytest mocks isolate notification behavior and SQLite temp databases isolate persistence tests. Selenium Chrome WebDriver tests the rendered interface in a real browser.

Measured non-Selenium run: **9 tests passed**, **82% combined coverage**. The Selenium smoke test passed separately on Chrome.

## 8. Configuration management

Use feature branches named `feature/<module-name>`. GitHub Actions is configured for both pushes and pull requests and installs dependencies, runs pytest, and reports coverage. Accepted and revised pull requests must be recorded through GitHub's pull request UI. A merge-conflict exercise should preserve the conflicting and resolved commits; record screenshots in `docs/evidence/`.

## 9. New tool

Swagger/OpenAPI was selected as the new self-directed tool. It provides interactive API documentation at `/docs` and a machine-readable contract at `/openapi.json`. The alternative was README-only endpoint documentation, which does not support direct request exploration and can drift from implementation. GitHub Actions remains included for sessional CI evidence, but Swagger is the independently learned tool to demonstrate real use.

## 10. Learning log

| Date | Learning goal | Resource | Challenge | Resolution |
|---|---|---|---|---|
| Day 1 | Flask application structure | Official Flask documentation | Organizing routes and templates | Used an application factory and test configuration |
| Day 2 | SQLite persistence | Official Python sqlite3 docs | Schema initialization and foreign keys | Added `init_schema()` and `PRAGMA foreign_keys` |
| Day 3 | pytest TDD and mocks | pytest documentation | Resetting singleton database state | Added `Database.reset()` for test isolation |
| Day 4 | Design patterns | Refactoring Guru; class teaching materials | Avoiding artificial pattern use | Applied Factory, Observer, and Singleton to real needs |
| Day 5 | Selenium | Selenium Python documentation | Starting Flask and finding browser drivers | Used Selenium Manager and a threaded local server |
| Day 6 | Swagger/OpenAPI | Official OpenAPI and Swagger UI docs | Keeping documentation synchronized | Added `/openapi.json` and `/docs` |
| Day 7 | GitHub Actions | Official Actions documentation | Version pinning and local parity | Defined Python 3.12 CI with requirements |

