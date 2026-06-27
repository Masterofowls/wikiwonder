"""Pytest configuration — use in-memory SQLite so tests do not hit Supabase."""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
