# app/schemas/employee.py
from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional
from app.schemas.base import TimeUserStampSchema


class EmployeeBase(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone_number: Optional[str] = Field(None, max_length=20)
    hire_date: date
    job_title: str = Field(..., min_length=1, max_length=100)
    salary: float = Field(..., gt=0)


class EmployeeCreate(EmployeeBase):
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    
    class Config:
        extra = "forbid"


class EmployeeUpdate(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(None, max_length=20)
    hire_date: Optional[date] = None
    job_title: Optional[str] = Field(None, min_length=1, max_length=100)
    salary: Optional[float] = Field(None, gt=0)
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    
    class Config:
        extra = "forbid"


class EmployeeOut(EmployeeBase, TimeUserStampSchema):
    id: int
    name: str
    user_id: Optional[int] = None
    department_id: Optional[int] = None
    
    class Config:
        from_attributes = True


# Basic user info for nested employee responses
class UserBasicForEmployee(BaseModel):
    """Basic user info for nested employee responses"""
    id: int
    username: Optional[str] = None
    email: EmailStr
    is_active: bool
    
    class Config:
        from_attributes = True


# Basic department info for nested employee responses
class DepartmentBasicForEmployee(BaseModel):
    """Basic department info for nested employee responses"""
    id: int
    name: str
    code: str
    location: Optional[str] = None
    
    class Config:
        from_attributes = True


class EmployeeWithDetails(EmployeeOut):
    """Employee with user and department details"""
    user: Optional[UserBasicForEmployee] = None
    department: Optional[DepartmentBasicForEmployee] = None
    
    class Config:
        from_attributes = True


class PaginatedEmployees(BaseModel):
    count: int
    data: list[EmployeeOut]


class EmployeeListResponse(BaseModel):
    status: str
    result: PaginatedEmployees


class PaginatedEmployeesWithDetails(BaseModel):
    count: int
    data: list[EmployeeWithDetails]


class EmployeeListWithDetailsResponse(BaseModel):
    status: str
    result: PaginatedEmployeesWithDetails