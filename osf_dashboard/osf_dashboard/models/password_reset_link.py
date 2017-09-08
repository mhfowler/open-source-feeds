import datetime

from sqlalchemy import Column, Integer, String, \
    DateTime, Boolean

from osf_dashboard.models.database import Base


class PasswordResetLink(Base):
    """
    This table is used to store singe-use tokens for password reset
    """
    __tablename__ = 'resetlinks'
    reset_link_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    secret_link = Column(String(120), unique=True, nullable=False)
    expired = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.datetime.now)