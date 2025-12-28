"""
User/Account CRUD router.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import UserResponse, UserUpdate, UserList, Message
from ..auth import get_current_user, get_current_admin, get_password_hash
from ..exceptions import NotFoundError, ForbiddenError, ConflictError

router = APIRouter(prefix="/v1/users", tags=["Users"])


@router.get(
    "",
    response_model=UserList,
    summary="List all users"
)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Max records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of users.
    
    Requires authentication. Admin users can see all users.
    """
    query = db.query(User)
    
    # Filter by active status if provided
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return UserList(
        items=users,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile"
)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """Get the currently authenticated user's profile."""
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get user by ID"
)
async def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific user by ID. Requires authentication."""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundError("User", user_id)
    
    return user


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update user"
)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a user's profile.
    
    Users can only update their own profile.
    Admins can update any user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundError("User", user_id)
    
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise ForbiddenError("You can only update your own profile")
    
    # Check for email conflict
    if user_data.email and user_data.email != user.email:
        existing = db.query(User).filter(User.email == user_data.email).first()
        if existing:
            raise ConflictError("Email already in use", {"field": "email"})
    
    # Check for username conflict
    if user_data.username and user_data.username != user.username:
        existing = db.query(User).filter(User.username == user_data.username).first()
        if existing:
            raise ConflictError("Username already taken", {"field": "username"})
    
    # Update fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    return user


@router.delete(
    "/{user_id}",
    response_model=Message,
    summary="Delete user"
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a user account.
    
    Users can only delete their own account.
    Admins can delete any user.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise NotFoundError("User", user_id)
    
    # Check authorization
    if current_user.id != user_id and current_user.role != "admin":
        raise ForbiddenError("You can only delete your own account")
    
    db.delete(user)
    db.commit()
    
    return Message(message="User deleted successfully")
