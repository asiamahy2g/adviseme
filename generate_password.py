#!/usr/bin/env python3
"""Generate hashed passwords for auth_config.yaml."""

import streamlit_authenticator as stauth

# Generate hashed passwords
passwords = ["admin123"]  # Change this to your desired password
hashed_passwords = stauth.Hasher(passwords).generate()

print("Generated password hashes:")
for i, hashed in enumerate(hashed_passwords):
    print(f"  Password {i+1}: {hashed}")

print("\nCopy the hash above and paste it into auth_config.yaml")
print("Replace the PLACEHOLDER_HASH_CHANGE_ME with the generated hash")
