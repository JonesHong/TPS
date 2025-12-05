#!/usr/bin/env python3
"""Test app import."""
print("Starting import test...")

try:
    from tps.app import app
    print(f"SUCCESS: App loaded - {app.title}")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
