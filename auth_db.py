import sqlite3
from pathlib import Path
import bcrypt

DB_PATH = Path(__file__).parent / "users.db"

def init_db(db_path: Path = DB_PATH):
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

def create_user(username: str, password: str, db_path: Path = DB_PATH) -> bool:
    """
    Create a user. Returns True if created, False if user exists.
    """
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        conn.close()
        return False
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    password_hash = bcrypt.hashpw(password_bytes, salt).decode("utf-8")
    cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
    conn.commit()
    conn.close()
    return True

def verify_user(username: str, password: str, db_path: Path = DB_PATH) -> bool:
    """
    Verify username/password. Returns True on success, False otherwise.
    """
    init_db(db_path)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False
    stored_hash = row[0].encode("utf-8")
    return bcrypt.checkpw(password.encode("utf-8"), stored_hash)

# --- Simple CLI for manual testing ---
def signup_cli():
    username = input("Enter new username: ")
    password = input("Enter new password: ")
    if create_user(username, password):
        print("✅ Signup successful!")
    else:
        print("❌ Username already exists. Try another.")

def login_cli():
    username = input("Enter username: ")
    password = input("Enter password: ")
    if verify_user(username, password):
        print("✅ Login successful!")
    else:
        print("❌ Invalid username or password.")

def main():
    while True:
        print("\n=== MENU ===")
        print("1. Signup")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option (1-3): ")
        if choice == '1':
            signup_cli()
        elif choice == '2':
            login_cli()
        elif choice == '3':
            break
        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
