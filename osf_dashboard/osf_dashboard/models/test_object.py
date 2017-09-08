from sqlalchemy import Column, Integer, String

from osf_dashboard.models.database import Base


class TestObject(Base):
    """
    This object isn't necessary to the app.
    It's used by a helper route in helper_routes.py for convenience of confirming that
    the server has a database connection
    """
    __tablename__ = 'test'
    id = Column(Integer, primary_key=True)
    key = Column(String(100))
    value = Column(String(100))

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value

    def __repr__(self):
        return '<TestObject {}:{}>'.format(self.key, self.value)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
        }