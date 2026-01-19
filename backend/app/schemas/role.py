# app/schemas/role.py
from pydantic import BaseModel, Field
from typing import Optional, List
from app.schemas.base import TimeUserStampSchema


# ✅ Forward declare to avoid circular import
class PermissionOut(BaseModel):
    id: int
    name: str
    description: str
    code: str
    module_name: Optional[str] = None
    
    class Config:
        from_attributes = True


class RoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    description: str = Field(..., min_length=1)
    code: Optional[str] = Field(None, max_length=50)


class RoleCreate(RoleBase):
    permission_ids: Optional[List[int]] = []
    
    class Config:
        extra = "forbid"


class RoleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, min_length=1)
    code: Optional[str] = Field(None, max_length=50)
    permission_ids: Optional[List[int]] = None
    
    class Config:
        extra = "forbid"


class RoleOut(RoleBase, TimeUserStampSchema):
    id: int
    
    class Config:
        from_attributes = True


class RoleWithPermissions(RoleOut):
    """Role with permissions details"""
    permissions: List[PermissionOut] = []
    
    class Config:
        from_attributes = True


# ✅ NEW: Role with user count
class RoleWithStats(RoleOut):
    """Role with statistics"""
    user_count: int = 0
    permission_count: int = 0
    
    class Config:
        from_attributes = True


class PaginatedRoles(BaseModel):
    count: int
    data: List[RoleOut]


class PaginatedRolesWithPermissions(BaseModel):
    count: int
    data: List[RoleWithPermissions]


class RoleListResponse(BaseModel):
    status: str
    result: PaginatedRoles


class RoleListWithPermissionsResponse(BaseModel):
    status: str
    result: PaginatedRolesWithPermissions