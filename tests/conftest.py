"""
Pytest fixtures for testing the e-commerce API.
"""

import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.database import Base, get_db
from src.main import app
from src.auth import get_password_hash, create_access_token
from src.models import User, Listing


# Use file-based SQLite for tests - ensures data is shared across sessions
TEST_DB_FILE = "/tmp/test_ecommerce.db"


@pytest.fixture(scope="function")
def db_engine():
    """Create a new engine for each test."""
    # Remove test db if exists
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)
    
    engine = create_engine(
        f"sqlite:///{TEST_DB_FILE}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()
    
    # Cleanup
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


@pytest.fixture(scope="function")
def db(db_engine):
    """Create a new database session for each test."""
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture(scope="function")
def client(db_engine):
    """Create test client with database override."""
    SessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    
    def override_get_db():
        session = SessionLocal()
        try:
            yield session
        finally:
            session.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(db) -> User:
    """Create a test user."""
    user = User(
        email="test@example.com",
        username="testuser",
        hashed_password=get_password_hash("Test1234"),
        role="user"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def admin_user(db) -> User:
    """Create a test admin user."""
    user = User(
        email="admin@example.com",
        username="adminuser",
        hashed_password=get_password_hash("Admin1234"),
        role="admin"
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def auth_header(test_user) -> dict:
    """Get authorization header for test user."""
    token = create_access_token(
        data={
            "sub": str(test_user.id),  # JWT spec requires sub to be string
            "username": test_user.username,
            "role": test_user.role
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_header(admin_user) -> dict:
    """Get authorization header for admin user."""
    token = create_access_token(
        data={
            "sub": str(admin_user.id),  # JWT spec requires sub to be string
            "username": admin_user.username,
            "role": admin_user.role
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def test_listing(db, test_user) -> Listing:
    """Create a test listing."""
    listing = Listing(
        title="Test Product",
        description="A test product description",
        price=99.99,
        quantity=10,
        category="electronics",
        seller_id=test_user.id
    )
    db.add(listing)
    db.commit()
    db.refresh(listing)
    return listing
