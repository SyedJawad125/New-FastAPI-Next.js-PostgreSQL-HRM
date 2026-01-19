# app/schemas/image.py
from pydantic import BaseModel, Field
from typing import Optional, TYPE_CHECKING
from app.schemas.base import TimeUserStampSchema


class ImageBase(BaseModel):
    name: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None


class ImageCreate(ImageBase):
    """Schema for image creation"""
    pass
    
    class Config:
        extra = "forbid"


class ImageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=30)
    description: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    
    class Config:
        extra = "forbid"


class ImageOut(ImageBase, TimeUserStampSchema):
    """Full image response with all mixin fields"""
    id: int
    image_path: str
    
    class Config:
        from_attributes = True


# Forward reference setup to avoid circular imports
if TYPE_CHECKING:
    from app.schemas.image_category import ImageCategoryOut


class ImageCategoryBasic(BaseModel):
    """Basic category info for nested responses"""
    id: int
    category: str
    
    class Config:
        from_attributes = True


class ImageWithCategory(ImageOut):
    """Image with category details"""
    category: Optional[ImageCategoryBasic] = None
    
    class Config:
        from_attributes = True


class PaginatedImages(BaseModel):
    count: int
    data: list[ImageOut]


class PaginatedImagesWithCategory(BaseModel):
    count: int
    data: list[ImageWithCategory]


class ImageListResponse(BaseModel):
    status: str
    result: PaginatedImages


class ImageListWithCategoryResponse(BaseModel):
    status: str
    result: PaginatedImagesWithCategory


class ImageUploadResponse(BaseModel):
    """Response after successful image upload"""
    status: str
    message: str
    data: ImageOut