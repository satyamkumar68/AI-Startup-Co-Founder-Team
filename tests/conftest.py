import os
import sys
import pytest

# Ensure root of project is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.main import app
from backend.app.db.session import get_async_db


@pytest.fixture(autouse=True)
def override_db_dependency():
    """Mock database dependency in unit/integration tests to run fast in-memory."""
    async def mock_get_db():
        yield None

    app.dependency_overrides[get_async_db] = mock_get_db
    yield
    app.dependency_overrides.pop(get_async_db, None)
