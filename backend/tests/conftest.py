
import pytest
from typing import Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from sqlalchemy.engine import Engine

from app.main import app
from app.db.database import Base
from app.db.database import get_db

# --- Test Database Setup ---
# Use an in-memory SQLite database for testing to keep tests fast and isolated.
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"


class BoolAnd:
    def __init__(self):
        self.result = True
    def step(self, value):
        if value is not None:
            self.result = self.result and bool(value)
    def finalize(self):
        return self.result

# This SQLAlchemy event listener is the core of the patch.
# It runs for every new connection and registers our custom function.
@event.listens_for(Engine, "connect")
def connect(dbapi_connection, connection_record):
    dbapi_connection.create_aggregate("bool_and", 1, BoolAnd)


engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)



# Create all database tables before tests run.
Base.metadata.create_all(bind=engine)


# --- Fixtures ---
@pytest.fixture(scope="function")
def db_session() -> Generator:
    """
    Pytest fixture to create a new database session for each test function.
    It ensures a clean state for every test.
    """
    connection = engine.connect()
    transaction = connection.begin()
    db = TestingSessionLocal(bind=connection)

    yield db

    db.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def test_client(db_session) -> Generator:
    """
    Pytest fixture to create a FastAPI TestClient that uses the test database.
    """

    def override_get_db():
        """Dependency override to use the test database session."""
        try:
            yield db_session
        finally:
            db_session.close()

    # Override the get_db dependency in the main app
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        yield client