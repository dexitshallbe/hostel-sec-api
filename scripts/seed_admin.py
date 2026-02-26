import os
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.security import hash_password
from db.models import Organization, User


def main():
    org_name = os.getenv("SEED_ORG", "HostelOrg")
    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com")
    admin_pw = os.getenv("SEED_ADMIN_PASSWORD", "admin123")
    admin_name = os.getenv("SEED_ADMIN_NAME", "Admin")

    db: Session = SessionLocal()

    org = db.query(Organization).filter(Organization.name == org_name).first()
    if not org:
        org = Organization(name=org_name)
        db.add(org)
        db.commit()
        db.refresh(org)

    user = db.query(User).filter(User.org_id == org.id, User.email == admin_email).first()
    if not user:
        user = User(
            org_id=org.id,
            name=admin_name,
            email=admin_email,
            password_hash=hash_password(admin_pw),
            role="ADMIN",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    print("Seeded:")
    print("ORG:", org.id, org.name)
    print("ADMIN:", user.id, user.email, user.role)


if __name__ == "__main__":
    main()