#!/usr/bin/env python3
"""
Create default admin user for RevCopy admin panel.
This script creates a default administrator account that can be used to log into the admin panel.
"""

import asyncio
import sys
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.models.user import User, UserRole, UserStatus
from app.core.security import get_password_hash


async def create_default_admin():
    """Create default admin user if it doesn't exist."""
    
    # Default admin credentials
    DEFAULT_ADMIN_EMAIL = "admin@revcopy.com"
    DEFAULT_ADMIN_PASSWORD = "admin123"
    DEFAULT_ADMIN_NAME = "System Administrator"
    
    try:
        async for db in get_async_session():
            # Check if admin already exists with this email
            result = await db.execute(
                select(User).where(User.email == DEFAULT_ADMIN_EMAIL)
            )
            existing_admin = result.scalar_one_or_none()
            
            # Also check if any admin user exists
            admin_result = await db.execute(
                select(User).where(User.role == UserRole.ADMIN)
            )
            any_admin = admin_result.scalar_one_or_none()
            
            if existing_admin:
                print(f"✅ Admin user already exists: {DEFAULT_ADMIN_EMAIL}")
                print(f"   ID: {existing_admin.id}")
                print(f"   Username: {existing_admin.username}")
                print(f"   Role: {existing_admin.role}")
                print(f"   Status: {existing_admin.status}")
                print(f"   Is Admin: {existing_admin.is_admin}")
                
                # Update to admin role if not already admin
                if not existing_admin.is_admin:
                    print("   ⬆️ Upgrading user to admin role...")
                    existing_admin.role = UserRole.ADMIN
                    existing_admin.status = UserStatus.ACTIVE
                    existing_admin.is_verified = True
                    await db.commit()
                    print(f"   ✅ User upgraded to admin!")
                
                return
            
            # Check if there's already an admin user with different email
            if any_admin and any_admin.email != DEFAULT_ADMIN_EMAIL:
                print(f"✅ An admin user already exists: {any_admin.email}")
                print(f"   ID: {any_admin.id}")
                print(f"   Username: {any_admin.username}")
                print(f"   Role: {any_admin.role}")
                print(f"   You can use this admin account or create a new one manually.")
                return
            
            # Create new admin user
            admin = User(
                email=DEFAULT_ADMIN_EMAIL,
                username="admin",
                first_name="System",
                last_name="Administrator",
                hashed_password=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role=UserRole.ADMIN,
                status=UserStatus.ACTIVE,
                is_verified=True,
            )
            
            db.add(admin)
            await db.commit()
            await db.refresh(admin)
            
            print("🎉 Default admin user created successfully!")
            print(f"   Email: {DEFAULT_ADMIN_EMAIL}")
            print(f"   Password: {DEFAULT_ADMIN_PASSWORD}")
            print(f"   Username: {admin.username}")
            print(f"   Full Name: {admin.full_name}")
            print(f"   Role: {UserRole.ADMIN}")
            print(f"   Status: {UserStatus.ACTIVE}")
            print(f"   ID: {admin.id}")
            print(f"   Is Admin: {admin.is_admin}")
            print()
            print("⚠️  IMPORTANT: Please change the default password after first login!")
            print("   You can do this through the admin panel or by running this script again with different credentials.")
            
    except Exception as e:
        print(f"❌ Error creating admin user: {e}")
        sys.exit(1)


async def main():
    """Main function."""
    print("🔧 Creating default admin user for RevCopy...")
    print()
    
    await create_default_admin()
    
    print()
    print("✅ Setup complete! You can now log into the admin panel at:")
    print("   http://localhost:3001 (or 3002/3003 if port is in use)")
    print()


if __name__ == "__main__":
    asyncio.run(main()) 