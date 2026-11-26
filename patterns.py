from datetime import datetime


class AppointmentFactory:
    @staticmethod
    def create(type_name, appointment):
        if type_name == "standard":
            appointment["appointment_type"] = "Standard consultation"
            return appointment
        raise ValueError("Unknown appointment type")


class AppointmentObserver:
    def __init__(self, message, category="info"):
        self.message = message
        self.category = category
        self.timestamp = datetime.now().strftime("%I:%M %p")


class NotificationService:
    def __init__(self, max_items=30):
        self._max_items = max_items
        self._events = []
        self._next_id = 1

    def notify(self, observer):
        print(f"[NOTIFICATION] {observer.message}")
        entry = {
            "id": self._next_id,
            "message": observer.message,
            "category": getattr(observer, "category", "info"),
            "timestamp": getattr(observer, "timestamp", datetime.now().strftime("%I:%M %p")),
        }
        self._next_id += 1
        self._events.insert(0, entry)
        if len(self._events) > self._max_items:
            self._events = self._events[: self._max_items]

    def list_events(self):
        return list(self._events)

    def clear(self):
        self._events.clear()


class CashPayment:
    def pay(self, amount):
        return {"status": "paid", "payment_method": "cash", "amount": amount}


class CardPayment:
    def pay(self, amount):
        return {"status": "paid", "payment_method": "card", "amount": amount}


class BkashPayment:
    def pay(self, amount):
        return {"status": "paid", "payment_method": "bKash", "amount": amount}


class PaymentStrategyFactory:
    _strategies = {
        "cash": CashPayment,
        "card": CardPayment,
        "bkash": BkashPayment,
    }

    @classmethod
    def create(cls, method):
        strategy = cls._strategies.get(str(method).lower())
        if not strategy:
            raise ValueError("Payment method must be cash, card, or bKash")
        return strategy()


class ClinicUserFactory:
    @staticmethod
    def create(role, name, email):
        role = str(role).lower()
        if role not in ("patient", "doctor", "admin", "receptionist"):
            raise ValueError("Unknown clinic user role")
        return {"name": name, "email": email, "role": role}
