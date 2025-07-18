from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime, timezone

class Users(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email  = Column(String, index=True)
    password = Column(String, index=True)
    profile_image = Column(String, nullable=True)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    addresses = relationship("Addresses", back_populates="user", uselist=False, cascade="all, delete-orphan")
    
    def to_dict(self):
        """
        Convert the Users object to a dictionary, excluding hashed_password.

        Returns:
            dict: Dictionary representation of the user (excluding sensitive fields)
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "profile_image": self.profile_image,
            "address": self.addresses.to_dict() if self.addresses else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

class Addresses(Base):
    __tablename__ = 'addresses'

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True)
    state = Column(String, index=True)
    country = Column(String, index=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    user = relationship("Users", back_populates="addresses")

    def to_dict(self):
        """
        Convert the Addresses object to a dictionary.
        """
        return {
            "id": self.id,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }