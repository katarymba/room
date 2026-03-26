"""pytest configuration for backend tests."""
import sys
import os

# Provide required env vars before any app module is imported
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-unit-tests-only-32chars!")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")
os.environ.setdefault("POSTGRES_PASSWORD", "test-password-for-unit-tests-only")
os.environ.setdefault("DEBUG", "true")

# Ensure the backend app package is importable when running pytest from the
# backend/ directory or from the repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
