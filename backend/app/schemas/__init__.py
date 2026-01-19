# app/schemas/__init__.py
"""
Centralized schemas export
"""
from app.schemas.user import (
    UserCreate, UserUpdate, UserOut, UserWithRole,
    UserWithEmployee, UserWithPermissions, UserDetailed,
    PaginatedUsers, UserListResponse,
    LoginRequest, TokenResponse, TokenData
)
from app.schemas.employee import (
    EmployeeCreate, EmployeeUpdate, EmployeeOut, EmployeeWithDetails,  # Changed from EmployeeWithUser
    PaginatedEmployees, EmployeeListResponse,
    PaginatedEmployeesWithDetails, EmployeeListWithDetailsResponse  # Updated names
)
from app.schemas.department import (  # ADD THIS IMPORT
    DepartmentCreate, DepartmentUpdate, DepartmentOut, DepartmentWithEmployees,
    PaginatedDepartments, DepartmentListResponse,
    PaginatedDepartmentsWithEmployees, DepartmentListWithEmployeesResponse
)
from app.schemas.permission import (
    PermissionCreate, PermissionUpdate, PermissionOut, PermissionWithRoles,
    PaginatedPermissions, PermissionListResponse,
    PaginatedPermissionsWithRoles, PermissionListWithRolesResponse
)
from app.schemas.role import (
    RoleCreate, RoleUpdate, RoleOut, RoleWithPermissions, RoleWithStats,
    PaginatedRoles, RoleListResponse,
    PaginatedRolesWithPermissions, RoleListWithPermissionsResponse
)
from app.schemas.image_category import (
    ImageCategoryCreate, ImageCategoryUpdate, ImageCategoryOut,
    ImageCategoryWithImages, ImageCategoryWithStats,
    PaginatedImageCategories, ImageCategoryListResponse,
    PaginatedImageCategoriesWithImages, ImageCategoryListWithImagesResponse
)
from app.schemas.image import (
    ImageCreate, ImageUpdate, ImageOut, ImageWithCategory,
    PaginatedImages, ImageListResponse, ImageUploadResponse,
    PaginatedImagesWithCategory, ImageListWithCategoryResponse
)

__all__ = [
    # User
    "UserCreate", "UserUpdate", "UserOut", "UserWithRole",
    "UserWithEmployee", "UserWithPermissions", "UserDetailed",
    "PaginatedUsers", "UserListResponse",
    "LoginRequest", "TokenResponse", "TokenData",
    
    # Employee
    "EmployeeCreate", "EmployeeUpdate", "EmployeeOut", "EmployeeWithDetails",  # Updated
    "PaginatedEmployees", "EmployeeListResponse",
    "PaginatedEmployeesWithDetails", "EmployeeListWithDetailsResponse",  # Updated
    
    # Department - ADD THIS SECTION
    "DepartmentCreate", "DepartmentUpdate", "DepartmentOut", "DepartmentWithEmployees",
    "PaginatedDepartments", "DepartmentListResponse",
    "PaginatedDepartmentsWithEmployees", "DepartmentListWithEmployeesResponse",
    
    # Permission
    "PermissionCreate", "PermissionUpdate", "PermissionOut", "PermissionWithRoles",
    "PaginatedPermissions", "PermissionListResponse",
    "PaginatedPermissionsWithRoles", "PermissionListWithRolesResponse",
    
    # Role
    "RoleCreate", "RoleUpdate", "RoleOut", "RoleWithPermissions", "RoleWithStats",
    "PaginatedRoles", "RoleListResponse",
    "PaginatedRolesWithPermissions", "RoleListWithPermissionsResponse",
    
    # Image Category
    "ImageCategoryCreate", "ImageCategoryUpdate", "ImageCategoryOut",
    "ImageCategoryWithImages", "ImageCategoryWithStats",
    "PaginatedImageCategories", "ImageCategoryListResponse",
    "PaginatedImageCategoriesWithImages", "ImageCategoryListWithImagesResponse",
    
    # Image
    "ImageCreate", "ImageUpdate", "ImageOut", "ImageWithCategory",
    "PaginatedImages", "ImageListResponse", "ImageUploadResponse",
    "PaginatedImagesWithCategory", "ImageListWithCategoryResponse",
]