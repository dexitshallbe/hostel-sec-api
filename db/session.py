from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import database_url

ENGINE = create_engine(database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=ENGINE, autoflush=False, autocommit=False)