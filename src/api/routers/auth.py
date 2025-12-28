"""
Authentication router with registration and login endpoints.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from ...core.database import get_db
from ...models.models import User
from ...schemas.schemas import UserCreate, UserResponse, Token, LoginRequest
from ...services.auth import get_password_hash, authenticate_user, create_access_token
from ...core.exceptions import ConflictError, UnauthorizedError

router = APIRouter(prefix="/v1/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user"
)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - **email**: Valid email address (must be unique)
    - **username**: Username (must be unique, 3-100 characters)
    - **password**: Password (min 8 chars, must contain uppercase, lowercase, digit)
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise ConflictError(
            message="Email already registered",
            details={"field": "email"}
        )
    
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise ConflictError(
            message="Username already taken",
            details={"field": "username"}
        )
    
    # Create new user
    user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user


@router.post(
    "/login",
    response_model=Token,
    summary="Login to get access token"
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT access token.
    
    Use the returned token in the Authorization header:
    `Authorization: Bearer <token>`
    """
    user = authenticate_user(db, form_data.username, form_data.password)
    
    if not user:
        raise UnauthorizedError("Invalid username or password")
    
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")
    
    access_token = create_access_token(
        data={
            "sub": str(user.id),  # JWT spec requires sub to be a string
            "username": user.username,
            "role": user.role
        }
    )
    
    return Token(access_token=access_token)
