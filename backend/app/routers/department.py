# app/api/routers/department.py
from fastapi import APIRouter, Depends, Request, status, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import Optional
import json
import os
import re

from app import database, schemas, models, oauth2
from app.utils import redis_client
from app.dependencies.permission import require


router = APIRouter(
    prefix="/api/departments",
    tags=['Departments']
)


def generate_department_code(name: str) -> str:
    """
    Generate department code from name.
    Examples:
        "Human Resources" -> "HR"
        "Information Technology" -> "IT"
        "Sales and Marketing" -> "SM"
        "Finance" -> "FIN"
    """
    # Remove special characters and extra spaces
    clean_name = re.sub(r'[^a-zA-Z\s]', '', name).strip()
    
    # Split into words
    words = clean_name.split()
    
    if len(words) == 1:
        # Single word: take first 3-4 letters
        code = words[0][:3].upper()
    elif len(words) == 2:
        # Two words: take first letter of each
        code = ''.join([word[0].upper() for word in words])
    else:
        # Multiple words: take first letter of each significant word
        # Skip common words like 'and', 'of', 'the'
        skip_words = {'and', 'of', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'}
        significant_words = [word for word in words if word.lower() not in skip_words]
        
        if len(significant_words) >= 2:
            code = ''.join([word[0].upper() for word in significant_words[:3]])
        else:
            code = ''.join([word[0].upper() for word in words[:3]])
    
    return code


def get_unique_department_code(db: Session, base_code: str) -> str:
    """
    Ensure department code is unique by appending a number if needed.
    Examples:
        "HR" -> "HR" (if available)
        "HR" -> "HR2" (if HR exists)
        "HR" -> "HR3" (if HR and HR2 exist)
    """
    code = base_code
    counter = 2
    
    while True:
        existing = db.query(models.Department).filter(
            models.Department.code == code
        ).first()
        
        if not existing:
            return code
        
        code = f"{base_code}{counter}"
        counter += 1


def invalidate_department_cache():
    """Invalidate all department-related cache entries"""
    if redis_client:
        try:
            for key in redis_client.scan_iter("departments_list:*"):
                redis_client.delete(key)
        except Exception as e:
            print(f"Cache invalidation error: {e}")


@router.get("/v1/department/", response_model=schemas.DepartmentListResponse, dependencies=[require("read_department")])
def get_departments(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    include_deleted: bool = False,
    include_employees: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user),
):
    """Get all departments with pagination and optional employee details"""
    try:
        # Create cache key
        cache_key = f"departments_list:{str(request.query_params)}:include_deleted:{include_deleted}:include_employees:{include_employees}"

        # Try Redis cache
        if redis_client and not include_deleted:
            cached = redis_client.get(cache_key)
            if cached:
                print("✅ Cache hit")
                cached_data = json.loads(cached)
                schema_class = schemas.DepartmentWithEmployees if include_employees else schemas.DepartmentOut
                serialized_data = [
                    schema_class(**dept) for dept in cached_data["data"]
                ]
                return {
                    "status": "success",
                    "result": {
                        "count": cached_data["count"],
                        "data": serialized_data
                    }
                }

        # Query based on include_deleted flag
        if include_deleted:
            query = models.Department.get_all_including_deleted(db)
        else:
            query = models.Department.get_active(db)

        # Apply search filter if provided
        search = request.query_params.get("search")
        if search:
            query = query.filter(
                (models.Department.name.ilike(f"%{search}%")) |
                (models.Department.code.ilike(f"%{search}%")) |
                (models.Department.location.ilike(f"%{search}%"))
            )
        
        total = query.count()
        departments = query.offset(skip).limit(limit).all()

        # Convert to Pydantic
        if include_employees:
            serialized_data = [schemas.DepartmentWithEmployees.from_orm(dept) for dept in departments]
        else:
            serialized_data = [schemas.DepartmentOut.from_orm(dept) for dept in departments]

        response_data = {
            "status": "success",
            "result": {
                "count": total,
                "data": serialized_data
            }
        }

        # Cache response
        if redis_client and not include_deleted:
            ttl = int(os.getenv("REDIS_CACHE_TTL", "300"))
            redis_client.setex(
                cache_key,
                ttl,
                json.dumps({
                    "count": total,
                    "data": [dept.model_dump() for dept in serialized_data]
                }, default=str)
            )

        return response_data

    except Exception as e:
        print(f"❌ Error in get_departments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/v1/department/{id}", response_model=schemas.DepartmentWithEmployees, dependencies=[require("read_department")])
def get_department(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Get department by ID with employee details"""
    department = db.query(models.Department).filter(
        models.Department.id == id,
        models.Department.deleted == False
    ).first()
    
    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {id} not found"
        )
    
    return department


@router.post("/v1/department/", 
            status_code=status.HTTP_201_CREATED, 
            response_model=schemas.DepartmentOut, 
            dependencies=[require("create_department")])
def create_department(
    department: schemas.DepartmentCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Create a new department with auto-generated code"""
    try:
        # Check if name already exists
        existing_name = db.query(models.Department).filter(
            models.Department.name == department.name
        ).first()
        
        if existing_name and not existing_name.deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Department with this name already exists"
            )
        
        if existing_name and existing_name.deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A department with this name was previously registered. Please use a different name."
            )

        # Generate unique department code from name
        base_code = generate_department_code(department.name)
        unique_code = get_unique_department_code(db, base_code)

        # Create department with user tracking and auto-generated code
        department_data = department.model_dump()
        new_department = models.Department(
            **department_data,
            code=unique_code,  # Auto-generated code
            created_by_user_id=current_user.id,
            updated_by_user_id=None
        )
        
        db.add(new_department)
        db.commit()
        db.refresh(new_department)
        
        # Invalidate cache
        invalidate_department_cache()
        
        return new_department

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating department: {str(e)}"
        )


@router.patch("/v1/department/{id}", response_model=schemas.DepartmentOut, dependencies=[require("update_department")])
def update_department(
    id: int,
    department_update: schemas.DepartmentUpdate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Update department information (code cannot be changed)"""
    try:
        department = db.query(models.Department).filter(
            models.Department.id == id,
            models.Department.deleted == False
        ).first()

        if not department:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Department with id {id} not found"
            )

        # Get update data
        update_data = department_update.dict(exclude_unset=True)
        
        # Check name uniqueness if name is being updated
        if "name" in update_data and update_data["name"] != department.name:
            existing = db.query(models.Department).filter(
                models.Department.name == update_data["name"],
                models.Department.id != id
            ).first()
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Department with this name already exists"
                )

        # Update fields
        for key, value in update_data.items():
            setattr(department, key, value)
        
        # Track who updated
        department.updated_by_user_id = current_user.id

        db.commit()
        db.refresh(department)
        
        # Invalidate cache
        invalidate_department_cache()

        return department

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating department: {str(e)}"
        )


@router.delete("/v1/department/{id}", status_code=status.HTTP_200_OK, dependencies=[require("delete_department")])
def delete_department(
    id: int,
    permanent: bool = False,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Soft delete department (or permanent delete if specified)"""
    department = db.query(models.Department).filter(
        models.Department.id == id
    ).first()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Department with id {id} not found"
        )

    # Check if department has active employees
    active_employees = db.query(models.Employee).filter(
        models.Employee.department_id == id,
        models.Employee.deleted == False
    ).count()

    if active_employees > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete department. It has {active_employees} active employee(s). Please reassign or remove employees first."
        )

    if permanent and current_user.is_superuser:
        # Permanent delete (hard delete) - only for superusers
        db.delete(department)
        db.commit()
        invalidate_department_cache()
        return {"message": "Department permanently deleted"}
    else:
        # Soft delete with user tracking
        department.soft_delete(user_id=current_user.id)
        db.commit()
        invalidate_department_cache()
        return {"message": "Department soft deleted successfully"}


@router.post("/v1/department/{id}/restore", response_model=schemas.DepartmentOut, dependencies=[require("update_department")])
def restore_department(
    id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Restore a soft-deleted department"""
    department = db.query(models.Department).filter(
        models.Department.id == id,
        models.Department.deleted == True
    ).first()

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Deleted department with id {id} not found"
        )

    department.restore()
    department.updated_by_user_id = current_user.id
    db.commit()
    db.refresh(department)
    
    # Invalidate cache
    invalidate_department_cache()

    return department


@router.post("/v1/department/bulk/upload/", dependencies=[require("create_department")])
async def upload_departments_bulk(
    file: UploadFile = File(...),
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(oauth2.get_current_user)
):
    """Bulk upload departments from Excel/CSV file (code auto-generated)"""
    try:
        import pandas as pd
        
        filename = file.filename or ""
        if filename.endswith(".xlsx"):
            df = pd.read_excel(file.file)
        elif filename.endswith(".csv"):
            df = pd.read_csv(file.file)
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only .xlsx and .csv files are supported"
            )

        df.columns = df.columns.str.strip()

        required_columns = {"name"}
        
        if not required_columns.issubset(df.columns):
            missing = required_columns - set(df.columns)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required columns: {missing}. Optional columns: description, location"
            )

        existing_names = {
            d.name for d in db.query(models.Department.name).filter(
                models.Department.deleted == False
            ).all()
        }
        
        added_count = 0
        skipped_rows = []
        validation_errors = {}

        for index, row in df.iterrows():
            row_errors = []
            try:
                name = str(row["name"]).strip()
                description = str(row.get("description", "")).strip() if pd.notna(row.get("description")) else None
                location = str(row.get("location", "")).strip() if pd.notna(row.get("location")) else None

                # Basic validation
                if not name or len(name) < 1:
                    row_errors.append("Invalid name")
                if name in existing_names:
                    row_errors.append("Department name already exists")

                if row_errors:
                    skipped_rows.append(index + 2)
                    validation_errors[index + 2] = row_errors
                    continue

                # Generate unique code
                base_code = generate_department_code(name)
                unique_code = get_unique_department_code(db, base_code)

                # Create department
                department = models.Department(
                    name=name,
                    code=unique_code,  # Auto-generated
                    description=description,
                    location=location,
                    created_by_user_id=current_user.id,
                    updated_by_user_id=None
                )
                
                db.add(department)
                added_count += 1
                existing_names.add(name)

            except Exception as e:
                skipped_rows.append(index + 2)
                validation_errors[index + 2] = [f"Unexpected error: {str(e)}"]

        db.commit()
        
        # Invalidate cache
        invalidate_department_cache()

        return {
            "status": "success" if not skipped_rows else "partial_success",
            "message": f"{added_count} departments added with auto-generated codes. {len(skipped_rows)} rows skipped.",
            "added_count": added_count,
            "skipped_rows": skipped_rows,
            "validation_errors": validation_errors if validation_errors else None
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )