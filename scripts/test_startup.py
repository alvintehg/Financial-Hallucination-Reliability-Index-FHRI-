#!/usr/bin/env python3
"""Quick test to ensure server starts without crashing."""

import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("Testing server startup...")

# Load environment
from dotenv import load_dotenv
load_dotenv()

print("1. Importing server module...")
try:
    from src import server
    print("   OK - server module imported")
except Exception as e:
    print(f"   FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("2. Checking FastAPI app...")
try:
    app = server.app
    print(f"   OK - app is {type(app)}")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("3. Checking health endpoint...")
try:
    routes = [r.path for r in app.routes]
    if "/health" in routes:
        print("   OK - /health endpoint exists")
    else:
        print(f"   WARNING - /health not found. Routes: {routes}")
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("4. Checking ask endpoint...")
try:
    if "/ask" in routes:
        print("   OK - /ask endpoint exists")
    else:
        print(f"   FAILED - /ask not found")
        sys.exit(1)
except Exception as e:
    print(f"   FAILED: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("SERVER MODULE LOADS SUCCESSFULLY!")
print("="*60)
print("\nYou can now start the server with:")
print("  uvicorn src.server:app --reload --port 8000")
print("="*60)
