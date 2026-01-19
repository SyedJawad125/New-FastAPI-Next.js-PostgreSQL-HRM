# app/models/department.py
from sqlalchemy import Column, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.mixins import TimeUserStampMixin


class Department(TimeUserStampMixin, Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    description = Column(Text, nullable=True)
    location = Column(String(100), nullable=True)
    
    # Relationship to employees
    employees = relationship(
        "Employee",
        back_populates="department",
        cascade="all, delete-orphan"
    )