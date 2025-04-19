# models.py
fake_users_db = {
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$abcdefghijk1234567890abcdefg",  # bcrypt hash of "adminpass"
        "role": "admin"
    },
    "user": {
        "username": "user",
        "hashed_password": "$2b$12$abcdefghijk0987654321abcdefg",  # bcrypt hash of "userpass"
        "role": "user"
    }
}
