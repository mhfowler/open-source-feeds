import datetime

from sqlalchemy import Column, Integer, String, \
    DateTime, Boolean

from osf_dashboard.models.database import Base


class User(Base):
    """
    The main user object, used for authentication and for keeping track of user details
    """
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=True)
    password = Column(String(120), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    deleted = Column(Boolean, default=False, nullable=False)

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
        }