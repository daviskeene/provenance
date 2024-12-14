from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import datetime

from database import Base  # Import Base from database.py


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    start_time = Column(DateTime, default=datetime.datetime.utcnow)
    finalized = Column(Boolean, default=False)
    data_hash = Column(String, nullable=True)  # To store the hex digest of the data
    signature = Column(String, nullable=True)  # Base64 encoded signature

    events = relationship("Event", back_populates="session")


class Event(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    character = Column(String(1), nullable=False)

    session = relationship("Session", back_populates="events")
