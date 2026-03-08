"""
Unit tests for professor account creation.

Tests for Task 2.4: Implement professor account creation
Validates Requirements: 7.2, 7.3, 7.4, 2.1, 2.2, 2.3
"""

import pytest
import bcrypt
from database import create_professor, get_professor_by_username


@pytest.mark.database
@pytest.mark.unit
class TestProfessorAccountCreation:
    """Test suite for professor account creation functionality."""
    
    def test_create_professor_with_valid_credentials(self, temp_db):
        """Test creating a professor account with valid username and password."""
        username = "valid_user"
        password = "password123"
        
        result = create_professor(username, password)
        
        assert result is True, "Should successfully create professor account"
        
        # Verify professor was created in database
        professor = get_professor_by_username(username)
        assert professor is not None, "Professor should exist in database"
        assert professor['username'] == username
    
    def test_create_professor_hashes_password_with_bcrypt(self, temp_db):
        """Test that password is hashed with bcrypt and not stored as plain text."""
        username = "bcrypt_user"
        password = "mypassword123"
        
        result = create_professor(username, password)
        assert result is True
        
        # Retrieve professor from database
        professor = get_professor_by_username(username)
        password_hash = professor['password_hash']
        
        # Verify it's a bcrypt hash (starts with $2b$)
        assert password_hash.startswith('$2b$'), "Password should be bcrypt hashed"
        
        # Verify it's not the plain text password
        assert password_hash != password, "Password should not be stored as plain text"
        
        # Verify the hash can be verified with bcrypt
        assert bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')), "Hash should verify correctly"
    
    def test_create_professor_generates_unique_salts(self, temp_db):
        """Test that creating two accounts with same password generates different hashes."""
        password = "samepassword123"
        
        # Create two professors with same password
        result1 = create_professor("user1", password)
        result2 = create_professor("user2", password)
        
        assert result1 is True
        assert result2 is True
        
        # Retrieve both professors
        prof1 = get_professor_by_username("user1")
        prof2 = get_professor_by_username("user2")
        
        # Hashes should be different due to unique salts
        assert prof1['password_hash'] != prof2['password_hash'], \
            "Same password should produce different hashes with unique salts"
    
    def test_create_professor_rejects_short_password(self, temp_db):
        """Test that passwords shorter than 8 characters are rejected."""
        username = "shortpass_user"
        short_passwords = ["", "a", "ab", "abc", "1234567"]  # All < 8 chars
        
        for password in short_passwords:
            with pytest.raises(ValueError, match="at least 8 characters"):
                create_professor(username, password)
    
    def test_create_professor_accepts_8_char_password(self, temp_db):
        """Test that exactly 8 character password is accepted."""
        username = "eightchar_user"
        password = "12345678"  # Exactly 8 chars
        
        result = create_professor(username, password)
        assert result is True, "8 character password should be accepted"
    
    def test_create_professor_accepts_long_password(self, temp_db):
        """Test that long passwords are accepted."""
        username = "longpass_user"
        password = "a" * 100  # Very long password
        
        result = create_professor(username, password)
        assert result is True, "Long passwords should be accepted"
    
    def test_create_professor_validates_username_format_alphanumeric(self, temp_db):
        """Test that usernames with only alphanumeric characters are accepted."""
        valid_usernames = [
            "user123",
            "TestUser",
            "abc",
            "ABC123xyz",
            "user2024"
        ]
        
        for i, username in enumerate(valid_usernames):
            result = create_professor(username, f"password{i}123")
            assert result is True, f"Username '{username}' should be accepted"
    
    def test_create_professor_validates_username_format_with_hyphens(self, temp_db):
        """Test that usernames with hyphens are accepted."""
        valid_usernames = [
            "test-user",
            "user-123",
            "my-test-user",
            "a-b-c"
        ]
        
        for i, username in enumerate(valid_usernames):
            result = create_professor(username, f"password{i}123")
            assert result is True, f"Username '{username}' with hyphens should be accepted"
    
    def test_create_professor_validates_username_format_with_underscores(self, temp_db):
        """Test that usernames with underscores are accepted."""
        valid_usernames = [
            "test_user",
            "user_123",
            "my_test_user",
            "a_b_c"
        ]
        
        for i, username in enumerate(valid_usernames):
            result = create_professor(username, f"password{i}123")
            assert result is True, f"Username '{username}' with underscores should be accepted"
    
    def test_create_professor_rejects_invalid_username_formats(self, temp_db):
        """Test that usernames with invalid characters are rejected."""
        invalid_usernames = [
            "user@test",      # @ symbol
            "user.name",      # period
            "user name",      # space
            "user!123",       # exclamation
            "user#tag",       # hash
            "user$money",     # dollar sign
            "user%percent",   # percent
            "user&and",       # ampersand
            "user*star",      # asterisk
            "user(paren",     # parenthesis
            "user+plus",      # plus
            "user=equals",    # equals
            "user[bracket",   # bracket
            "user{brace",     # brace
            "user|pipe",      # pipe
            "user\\slash",    # backslash
            "user/forward",   # forward slash
            "user:colon",     # colon
            "user;semi",      # semicolon
            "user'quote",     # single quote
            'user"double',    # double quote
            "user<less",      # less than
            "user>greater",   # greater than
            "user?question",  # question mark
            "user,comma",     # comma
        ]
        
        for username in invalid_usernames:
            with pytest.raises(ValueError, match="alphanumeric characters, hyphens, and underscores"):
                create_professor(username, "password123")
    
    def test_create_professor_rejects_duplicate_username(self, temp_db):
        """Test that duplicate usernames are rejected."""
        username = "duplicate_user"
        password1 = "password123"
        password2 = "different456"
        
        # Create first professor
        result1 = create_professor(username, password1)
        assert result1 is True, "First account creation should succeed"
        
        # Try to create second professor with same username
        result2 = create_professor(username, password2)
        assert result2 is False, "Duplicate username should be rejected"
        
        # Verify only one professor exists
        professor = get_professor_by_username(username)
        assert professor is not None, "Original professor should still exist"
        
        # Verify the password is from the first account
        assert bcrypt.checkpw(password1.encode('utf-8'), professor['password_hash'].encode('utf-8')), \
            "Original password should still be valid"
    
    def test_create_professor_mixed_valid_characters(self, temp_db):
        """Test usernames with mixed valid characters (alphanumeric, hyphens, underscores)."""
        valid_usernames = [
            "User_Name-123",
            "test-user_2024",
            "My-Test_User123",
            "a1-b2_c3"
        ]
        
        for i, username in enumerate(valid_usernames):
            result = create_professor(username, f"password{i}123")
            assert result is True, f"Username '{username}' with mixed valid characters should be accepted"
    
    def test_create_professor_case_sensitive_usernames(self, temp_db):
        """Test that usernames are case-sensitive."""
        # Create professor with lowercase username
        result1 = create_professor("testuser", "password123")
        assert result1 is True
        
        # Create professor with uppercase username (should be different)
        result2 = create_professor("TESTUSER", "password456")
        assert result2 is True, "Usernames should be case-sensitive"
        
        # Verify both exist
        prof1 = get_professor_by_username("testuser")
        prof2 = get_professor_by_username("TESTUSER")
        
        assert prof1 is not None
        assert prof2 is not None
        assert prof1['professor_id'] != prof2['professor_id']
    
    def test_create_professor_empty_username(self, temp_db):
        """Test that empty username is rejected."""
        with pytest.raises(ValueError, match="alphanumeric characters, hyphens, and underscores"):
            create_professor("", "password123")
    
    def test_create_professor_stores_creation_timestamp(self, temp_db):
        """Test that created_at timestamp is stored."""
        username = "timestamp_user"
        password = "password123"
        
        result = create_professor(username, password)
        assert result is True
        
        professor = get_professor_by_username(username)
        assert professor['created_at'] is not None, "created_at timestamp should be stored"
    
    def test_create_professor_returns_true_on_success(self, temp_db):
        """Test that create_professor returns True on successful creation."""
        result = create_professor("success_user", "password123")
        assert result is True, "Should return True on success"
    
    def test_create_professor_returns_false_on_duplicate(self, temp_db):
        """Test that create_professor returns False when username already exists."""
        username = "existing_user"
        
        # Create first account
        result1 = create_professor(username, "password123")
        assert result1 is True
        
        # Try to create duplicate
        result2 = create_professor(username, "password456")
        assert result2 is False, "Should return False when username exists"
