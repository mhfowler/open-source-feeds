import random

from hello_models.models import TestObject


def get_test_objects(db):
    test_objects = TestObject.query.all()
    return test_objects


def create_test_object(db):
    t = TestObject(key='test', value=str(random.randint(0, 1000)))
    db.session.add(t)
    db.session.commit()