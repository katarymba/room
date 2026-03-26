"""pytest configuration for backend tests."""
import sys
import os

# Provide required env vars before any app module is imported
os.environ.setdefault("SECRET_KEY", "f47ac10b-58cc-4372-a567-0e02b2c3d479-aXk9mQ3r")
os.environ.setdefault("DATABASE_URL", "postgresql://test:test@localhost:5432/test")

# Ensure the backend app package is importable when running pytest from the
# backend/ directory or from the repository root.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
