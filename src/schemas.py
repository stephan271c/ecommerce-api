"""
Pydantic schemas for request/response validation.

Schemas handle data validation, serialization, and documentation.
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ============== User Schemas ==============

class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=8, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v


class UserUpdate(BaseModel):
    """Schema for updating user profile."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response (excludes password)."""
    id: int
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class UserList(BaseModel):
    """Paginated list of users."""
    items: List[UserResponse]
    total: int
    skip: int
    limit: int


# ============== Listing Schemas ==============

class ListingBase(BaseModel):
    """Base listing schema with common fields."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    price: float = Field(..., gt=0)
    quantity: int = Field(default=1, ge=0)
    category: Optional[str] = Field(None, max_length=100)


class ListingCreate(ListingBase):
    """Schema for creating a listing."""
    pass


class ListingUpdate(BaseModel):
    """Schema for updating a listing."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    category: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


class ListingResponse(ListingBase):
    """Schema for listing response."""
    id: int
    seller_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ListingList(BaseModel):
    """Paginated list of listings."""
    items: List[ListingResponse]
    total: int
    skip: int
    limit: int


# ============== Auth Schemas ==============

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Data extracted from JWT token."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


# ============== Common Schemas ==============

class Message(BaseModel):
    """Simple message response."""
    message: str


class HealthCheck(BaseModel):
    """Health check response."""
    status: str
    version: str


class DetailedHealthCheck(BaseModel):
    """Detailed health check with dependencies."""
    status: str
    version: str
    database: str
    redis: str
