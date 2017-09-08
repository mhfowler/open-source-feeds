"""
These helper functions are used by the /api/test_db/ route in helper_routes.py which is
not necessary to the app, but is useful for quickly debugging/confirming that a server
is connected to the database
"""
import random

from osf_dashboard.models import TestObject


def get_test_objects(db_session):
    test_objects = db_session.query(TestObject).all()
    return test_objects


def create_test_object(db_session):
    t = TestObject(key='test', value=str(random.randint(0, 1000)))
    db_session.add(t)
    db_session.commit()