import gc
import os
import shutil
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app import create_app
from database import Database


@pytest.fixture
def database():
    Database.reset()
    directory = tempfile.mkdtemp()
    path = os.path.join(directory, "test.db")
    db = Database(path)
    db.init_schema()
    yield db
    Database.reset()
    gc.collect()
    shutil.rmtree(directory, ignore_errors=True)


@pytest.fixture
def client(database):
    app = create_app(database)
    app.config.update(TESTING=True)
    test_client = app.test_client()
    test_client.post(
        "/signup",
        json={
            "name": "Test Administrator",
            "email": "admin@example.com",
            "password": "password123",
        },
    )
    return test_client
