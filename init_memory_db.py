#!/usr/bin/env python3
"""
Initialize the in-memory database and create test users
"""
from app.services.user_service import user_service
from app.models.enums import UserRole


def create_test_users():
    """Create test users for development"""
    print("👥 Creating test users...")
    
    try:
        # Create State Government user
        state_user = user_service.create_user(
            username="state_user",
            email="state@example.com",
            password="password123",
            role=UserRole.STATE_USER,
            department="Roads",
            state="Maharashtra"
        )
        print("✅ Created State Government user (username: state_user, password: password123)")
        
        # Create MDONER user
        mdoner_user = user_service.create_user(
            username="mdoner_user",
            email="mdoner@example.com",
            password="password123",
            role=UserRole.MDONER_USER
        )
        print("✅ Created MDONER user (username: mdoner_user, password: password123)")
        
        print("✅ Test users created successfully")
        return True
        
    except Exception as e:
        print(f"❌ Error creating test users: {e}")
        return False


def main():
    """Main initialization function"""
    print("🚀 Initializing Government Project Platform In-Memory Database")
    print("=" * 60)
    
    try:
        success = create_test_users()
        if success:
            print("\n🎉 In-memory database initialization completed successfully!")
            print("\n📝 Test Credentials:")
            print("State User - Username: state_user, Password: password123")
            print("MDONER User - Username: mdoner_user, Password: password123")
            print("\n🚀 You can now start the backend server with:")
            print("uvicorn main:app --reload --host 0.0.0.0 --port 8000")
            return True
        else:
            print("❌ Database initialization failed")
            return False
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)