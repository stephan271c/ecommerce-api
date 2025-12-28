"""
Authentication utilities for JWT and password handling.

Features:
- Password hashing with bcrypt
- JWT token creation and verification
- FastAPI dependencies for authentication
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from ..core.config import get_settings
from ..core.database import get_db
from ..models.models import User
from ..schemas.schemas import TokenData
from ..core.exceptions import UnauthorizedError, ForbiddenError

settings = get_settings()

# OAuth2 scheme for bearer token extraction
# auto_error=False allows cookie-based auth to work when no Bearer token is provided
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    return bcrypt.checkpw(
        plain_password.encode('utf-8'), 
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Payload data to encode in the token
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with user information
        
    Raises:
        UnauthorizedError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        # sub claim must be string per JWT spec, convert to int
        sub = payload.get("sub")
        user_id = int(sub) if sub is not None else None
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if user_id is None:
            raise UnauthorizedError("Invalid token")
            
        return TokenData(user_id=user_id, username=username, role=role)
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise UnauthorizedError(f"Invalid token")


async def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    FastAPI dependency to get the current authenticated user.
    
    Supports both:
    - Bearer token in Authorization header (for API clients)
    - HttpOnly cookie (for browser clients)
    
    Args:
        request: The incoming request (for cookie access)
        token: JWT token from Authorization header
        db: Database session
        
    Returns:
        Current authenticated User
        
    Raises:
        UnauthorizedError: If authentication fails
    """
    # Try cookie first if no Bearer token provided
    auth_token = token
    if not auth_token or auth_token == "":
        cookie_token = request.cookies.get("access_token")
        if cookie_token:
            auth_token = cookie_token
    
    if not auth_token:
        raise UnauthorizedError("Not authenticated")
    
    token_data = decode_token(auth_token)
    user = db.query(User).filter(User.id == token_data.user_id).first()
    
    if user is None:
        raise UnauthorizedError("User not found")
    if not user.is_active:
        raise UnauthorizedError("User account is deactivated")
        
    return user


async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    FastAPI dependency to verify the current user is an admin.
    
    Args:
        current_user: The authenticated user
        
    Returns:
        Current user if they are an admin
        
    Raises:
        ForbiddenError: If user is not an admin
    """
    if current_user.role != "admin":
        raise ForbiddenError("Admin access required")
    return current_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Authenticate a user by username and password.
    
    Args:
        db: Database session
        username: Username to authenticate
        password: Plain text password
        
    Returns:
        User if authentication succeeds, None otherwise
    """
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
