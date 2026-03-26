"""pytest configuration for backend tests."""
import sys
import os

# Provide required env vars before any app module is imported
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

# Ensure the backend app package is importable when running pytest from the
# backend/ directory or from the repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Configure pytest-asyncio to auto-detect async test functions so that
# individual test methods do not need to be decorated with @pytest.mark.asyncio
# (though the decorator is still supported for backward compatibility).
import pytest

def pytest_configure(config):
    config.addinivalue_line(
        "markers", "asyncio: mark test as an asyncio coroutine"
    )
