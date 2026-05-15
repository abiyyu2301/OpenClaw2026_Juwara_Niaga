"""SQLAlchemy session + Base."""

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from settings import REPO_ROOT, settings


def _resolved_database_url() -> str:
    """Resolve a relative sqlite path against REPO_ROOT so the DB lives in
    the same place regardless of which directory you launch from."""
    url = settings.database_url
    if url.startswith("sqlite:///") and not url.startswith("sqlite:////"):
        rel = url.replace("sqlite:///", "", 1)
        if rel.startswith("./"):
            rel = rel[2:]
        abs_path = (REPO_ROOT / rel).resolve()
        abs_path.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{abs_path}"
    return url


engine = create_engine(
    _resolved_database_url(),
    connect_args={"check_same_thread": False} if settings.database_url.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
