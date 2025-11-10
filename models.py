from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class Event(Base):
    __tablename__ = "event"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Prize(Base):
    __tablename__ = "prize"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), nullable=False)
    name = Column(String, nullable=False)
    weight = Column(Integer, default=0)
    total_inventory = Column(Integer, default=0)
    remaining_inventory = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class Session(Base):
    __tablename__ = "session"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True, nullable=False)
    event_id = Column(Integer, ForeignKey("event.id"), nullable=False)
    ip_hash = Column(String, nullable=False)
    has_spun = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    spun_at = Column(DateTime, nullable=True)


class Spin(Base):
    __tablename__ = "spin"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("session.session_id"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("event.id"), nullable=False, index=True)
    slice_index = Column(Integer, nullable=False)
    label = Column(String, nullable=False)
    is_prize = Column(Boolean, default=False)
    prize_id = Column(Integer, ForeignKey("prize.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
