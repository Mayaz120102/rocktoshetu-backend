from sqlalchemy import (
    Column,
    Date,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)
from app.database import Base
from datetime import datetime, timezone
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, index=True, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="requester")
    phone = Column(String, nullable=True)
    blood_group = Column(String, nullable=True)
    city = Column(String, nullable=True)
    is_verified = Column(Boolean, nullable=False, default=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    is_available = Column(Boolean, nullable=False, default=True)
    last_donation_date = Column(Date, nullable=True)


class BloodRequests(Base):
    __tablename__ = "blood_requests"

    id = Column(
        Integer,
        index=True,
        primary_key=True,
    )
    requester_id = Column(Integer, ForeignKey("users.id"))
    patient_name = Column(String, nullable=False)
    blood_group = Column(String, nullable=False)
    units = Column(Integer, nullable=False)
    urgency = Column(String, nullable=False, default="normal")
    hospital_name = Column(String, nullable=False)
    city = Column(String, nullable=True)
    needed_by = Column(Date, nullable=False)
    status = Column(String, default="pending")
    created_at = Column(
        DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class DonorResponses(Base):
    __tablename__ = "donor_responses"
    __table_args__ = (
        UniqueConstraint("request_id", "donor_id"),
        )

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("blood_requests.id"), nullable=False)
    donor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String, default="responded")
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    request = relationship("BloodRequests")
    donor = relationship("Users")


class BloodStock(Base):
    __tablename__ = "blood_stock"
    __table_args__ = (
        UniqueConstraint("hospital_id", "blood_group"),
        )

    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    blood_group = Column(String, nullable=False)
    units = Column(Integer, default=0, nullable=False)
