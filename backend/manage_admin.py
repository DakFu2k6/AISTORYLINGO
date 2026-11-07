import sys
from sqlmodel import Session, select
from app.database import engine, create_db_and_tables
from app.models import User

if __name__ == "__main__":
    create_db_and_tables()
    email = sys.argv[1].strip().lower() if len(sys.argv) == 2 else ""
    with Session(engine) as db:
        user = db.exec(select(User).where(User.email == email)).first()
        if not user:
            raise SystemExit("Register the account first, then pass its email.")
        user.role = "admin"
        db.add(user)
        db.commit()
        print("Administrator role granted. Log in again.")
