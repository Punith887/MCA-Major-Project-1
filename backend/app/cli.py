from getpass import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError
from sqlalchemy import select

from app.core.security import hash_password
from app.database.connection import SessionLocal
from app.models.user import User, UserRole


def create_admin() -> None:
    full_name = input("Administrator full name: ").strip()
    email_input = input("Administrator email: ").strip()
    password = getpass("Administrator password (12+ characters): ")
    confirmation = getpass("Confirm password: ")

    if len(full_name) < 2:
        raise SystemExit("Full name must contain at least 2 characters.")
    try:
        email = str(TypeAdapter(EmailStr).validate_python(email_input)).lower()
    except ValidationError as exc:
        raise SystemExit("Enter a valid administrator email address.") from exc
    if len(password) < 12:
        raise SystemExit("Password must contain at least 12 characters.")
    if password != confirmation:
        raise SystemExit("Passwords do not match.")

    with SessionLocal() as db:
        if db.scalar(select(User.id).where(User.email == email)) is not None:
            raise SystemExit("An account with that email already exists.")
        admin = User(
            full_name=full_name,
            email=email,
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
        )
        db.add(admin)
        db.commit()
        print(f"Administrator account created for {email}.")


if __name__ == "__main__":
    create_admin()
