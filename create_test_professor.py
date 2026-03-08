"""
Script to create a test professor account for manual testing.

Usage: python create_test_professor.py
"""

import database

def main():
    # Initialize database
    database.initialize_database()
    
    # Create test professor account
    username = "test_professor"
    password = "password123"
    
    print(f"Creating test professor account...")
    print(f"Username: {username}")
    print(f"Password: {password}")
    
    try:
        success = database.create_professor(username, password)
        if success:
            print("✓ Test professor account created successfully!")
            print("\nYou can now log in to AdviseMe with:")
            print(f"  Username: {username}")
            print(f"  Password: {password}")
        else:
            print("✗ Failed to create account (username may already exist)")
            print("\nTrying to verify existing account...")
            prof = database.get_professor_by_username(username)
            if prof:
                print(f"✓ Account already exists with username: {username}")
                print("  You can use the existing credentials to log in")
    except ValueError as e:
        print(f"✗ Validation error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")

if __name__ == "__main__":
    main()
