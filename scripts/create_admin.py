#!/usr/bin/env python3
"""
CLI script to create an admin user.

Usage:
    python -m scripts.create_admin --email admin@example.com --username admin --password examplePass789
    
Or interactively:
    python -m scripts.create_admin
"""

import argparse
import getpass
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.database import SessionLocal
from src.models.models import User, UserRole
from src.services.auth import get_password_hash


def create_admin(email: str, username: str, password: str) -> bool:
    """
    Create an admin user in the database.
    
    Args:
        email: Admin email address
        username: Admin username
        password: Admin password (will be hashed)
        
    Returns:
        True if successful, False otherwise
    """
    db = SessionLocal()
    try:
        # Check if user already exists
        existing = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing:
            if existing.email == email:
                print(f"Error: Email '{email}' is already registered.")
            else:
                print(f"Error: Username '{username}' is already taken.")
            return False
        
        # Create admin user
        admin = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            role=UserRole.ADMIN.value
        )
        db.add(admin)
        db.commit()
        
        print(f"✓ Admin user '{username}' created successfully!")
        print(f"  Email: {email}")
        print(f"  Role: admin")
        return True
        
    except Exception as e:
        print(f"Error creating admin: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(
        description="Create an admin user for the application."
    )
    parser.add_argument("--email", "-e", help="Admin email address")
    parser.add_argument("--username", "-u", help="Admin username")
    parser.add_argument("--password", "-p", help="Admin password (not recommended, use interactive mode)")
    
    args = parser.parse_args()
    
    # Get values interactively if not provided
    email = args.email
    if not email:
        email = input("Enter admin email: ").strip()
        if not email:
            print("Error: Email is required.")
            sys.exit(1)
    
    username = args.username
    if not username:
        username = input("Enter admin username: ").strip()
        if not username:
            print("Error: Username is required.")
            sys.exit(1)
    
    password = args.password
    if not password:
        password = getpass.getpass("Enter admin password: ")
        if not password:
            print("Error: Password is required.")
            sys.exit(1)
        
        # Confirm password in interactive mode
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Error: Passwords do not match.")
            sys.exit(1)
    
    # Validate password strength (same rules as registration)
    if len(password) < 8:
        print("Error: Password must be at least 8 characters.")
        sys.exit(1)
    if not any(c.isupper() for c in password):
        print("Error: Password must contain at least one uppercase letter.")
        sys.exit(1)
    if not any(c.islower() for c in password):
        print("Error: Password must contain at least one lowercase letter.")
        sys.exit(1)
    if not any(c.isdigit() for c in password):
        print("Error: Password must contain at least one digit.")
        sys.exit(1)
    
    success = create_admin(email, username, password)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
