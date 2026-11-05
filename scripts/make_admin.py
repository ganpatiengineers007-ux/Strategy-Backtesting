#!/usr/bin/env python3
"""ADMIN_USER aur ADMIN_PASSWORD_HASH banane ke liye script.
Chalane ke liye: python scripts/make_admin.py
Password hidden prompt se liya jayega (stdin pe nahi dikhega)."""
import getpass
import os
import sys
from pathlib import Path

import bcrypt


def hash_password(password: str) -> str:
    """Password ko bcrypt se hash karo."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode(), salt).decode()


def verify_password(password: str, hash_: str) -> bool:
    """Password verify karo."""
    return bcrypt.checkpw(password.encode(), hash_.encode())


def main():
    env_path = Path(__file__).resolve().parent.parent / "infra" / ".env"
    env_path.parent.mkdir(parents=True, exist_ok=True)

    print("Admin user banane ke liye details daalein:")
    username = input("Username: ").strip()
    if not username:
        print("Username khali nahi ho sakta", file=sys.stderr)
        sys.exit(1)

    while True:
        password = getpass.getpass("Password (kam se kam 10 characters): ")
        if len(password) < 10:
            print("Password kam se kam 10 characters ka hona chahiye", file=sys.stderr)
            continue
        confirm = getpass.getpass("Password dobara daalein: ")
        if password != confirm:
            print("Passwords match nahi kiye", file=sys.stderr)
            continue
        break

    password_hash = hash_password(password)

    # .env file update karo
    lines = []
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()

    # Purane ADMIN_ lines hatao
    lines = [l for l in lines if not l.startswith("ADMIN_USER=") and not l.startswith("ADMIN_PASSWORD_HASH=")]

    lines.append(f"ADMIN_USER={username}")
    # Single quotes: Docker Compose .env me `$2b$12$...` ko interpolate hone se bachao.
    lines.append(f"ADMIN_PASSWORD_HASH='{password_hash}'")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nDone! {env_path} me likha gaya:")
    print(f"  ADMIN_USER={username}")
    print(f"  ADMIN_PASSWORD_HASH={password_hash[:20]}...")

    # Verify karo
    if verify_password(password, password_hash):
        print("\nVerify: Password hash sahi hai ✓")
    else:
        print("\nERROR: Hash verify nahi hua!", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()