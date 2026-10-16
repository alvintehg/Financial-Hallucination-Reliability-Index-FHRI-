#!/usr/bin/env python3
"""
Comprehensive setup checker for LLM Financial Chatbot.
Run this before starting the server to catch all issues.
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("="*60)
print("LLM Financial Chatbot - Setup Checker")
print("="*60)

issues = []
warnings = []

# 1. Check Python version
print("\n[1/10] Checking Python version...")
if sys.version_info < (3, 8):
    issues.append(f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}")
else:
    print(f"  OK: Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

# 2. Check critical packages
print("\n[2/10] Checking critical packages...")
required_packages = [
    ('dotenv', 'python-dotenv'),
    ('fastapi', 'fastapi'),
    ('uvicorn', 'uvicorn'),
    ('requests', 'requests'),
    ('sklearn', 'scikit-learn'),
    ('pydantic', 'pydantic'),
]

for module_name, package_name in required_packages:
    try:
        __import__(module_name)
        print(f"  OK: {package_name}")
    except ImportError:
        issues.append(f"Missing package: {package_name} (pip install {package_name})")

# 3. Check optional packages
print("\n[3/10] Checking optional packages...")
optional_packages = [
    ('torch', 'torch'),
    ('transformers', 'transformers'),
    ('sentence_transformers', 'sentence-transformers'),
]

for module_name, package_name in optional_packages:
    try:
        __import__(module_name)
        print(f"  OK: {package_name}")
    except ImportError:
        warnings.append(f"Optional package not installed: {package_name} (hallucination detection disabled)")

# 4. Check .env file
print("\n[4/10] Checking .env file...")
env_path = PROJECT_ROOT / ".env"
if not env_path.exists():
    issues.append(".env file not found. Copy .env.template to .env and add your API keys")
else:
    print(f"  OK: .env exists")

    # Load and check API keys
    from dotenv import load_dotenv
    load_dotenv(env_path)

    deepseek_key = os.getenv("DEEPSEEK_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if deepseek_key and deepseek_key != "sk-your-deepseek-key-here":
        print(f"  OK: DEEPSEEK_API_KEY is set")
    elif openai_key and openai_key != "sk-your-openai-key-if-you-have-one":
        print(f"  OK: OPENAI_API_KEY is set (DeepSeek not configured)")
        warnings.append("DEEPSEEK_API_KEY not set, will use OpenAI as primary")
    else:
        warnings.append("No API keys configured - will run in demo mode only")

# 5. Check data directory
print("\n[5/10] Checking data directory...")
data_dir = PROJECT_ROOT / "data"
if not data_dir.exists():
    issues.append("data/ directory not found")
else:
    print(f"  OK: data/ directory exists")

# 6. Check passages.txt
print("\n[6/10] Checking passages.txt...")
passages_file = data_dir / "passages.txt"
if not passages_file.exists():
    issues.append("data/passages.txt not found - retrieval will fail")
else:
    content = passages_file.read_text(encoding='utf-8')
    if not content.strip():
        issues.append("data/passages.txt is empty - add knowledge base content")
    else:
        passages = [p for p in content.split('\n\n') if p.strip()]
        print(f"  OK: Found {len(passages)} passages")

# 7. Check models directory
print("\n[7/10] Checking models directory...")
models_dir = PROJECT_ROOT / "models"
if not models_dir.exists():
    print(f"  Creating models/ directory...")
    models_dir.mkdir(exist_ok=True)
print(f"  OK: models/ directory exists")

# 8. Check TF-IDF index
print("\n[8/10] Checking TF-IDF index...")
tfidf_vec = models_dir / "tfidf_vectorizer.pkl"
passages_pkl = models_dir / "passages.pkl"

if not tfidf_vec.exists() or not passages_pkl.exists():
    print(f"  Building TF-IDF index...")
    try:
        from src.retrieval import rebuild_tfidf_index
        rebuild_tfidf_index(str(passages_file))
        print(f"  OK: TF-IDF index built")
    except Exception as e:
        issues.append(f"Failed to build TF-IDF index: {e}")
else:
    print(f"  OK: TF-IDF index exists")

# 9. Test module imports
print("\n[9/10] Testing module imports...")
try:
    from src.retrieval import query_index
    print(f"  OK: src.retrieval")
except Exception as e:
    issues.append(f"Cannot import src.retrieval: {e}")

try:
    from src.hallucination_entropy import MCEncoder
    print(f"  OK: src.hallucination_entropy")
except Exception as e:
    warnings.append(f"Cannot import MCEncoder (optional): {e}")

try:
    from src.nli_infer import load_model
    print(f"  OK: src.nli_infer")
except Exception as e:
    warnings.append(f"Cannot import NLI (optional): {e}")

# 10. Test server module loads
print("\n[10/10] Testing server module...")
try:
    # Don't actually import to avoid hanging
    import ast
    server_file = PROJECT_ROOT / "src" / "server.py"
    with open(server_file, 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print(f"  OK: server.py syntax valid")
except Exception as e:
    issues.append(f"server.py has syntax errors: {e}")

# Summary
print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if issues:
    print(f"\nCRITICAL ISSUES ({len(issues)}):")
    for i, issue in enumerate(issues, 1):
        print(f"  {i}. {issue}")

if warnings:
    print(f"\nWARNINGS ({len(warnings)}):")
    for i, warning in enumerate(warnings, 1):
        print(f"  {i}. {warning}")

if not issues and not warnings:
    print("\nALL CHECKS PASSED!")
    print("\nYou can now start the server:")
    print("  uvicorn src.server:app --reload --port 8000")
elif not issues:
    print("\nSETUP OK (with warnings)")
    print("\nYou can start the server, but some features may be limited:")
    print("  uvicorn src.server:app --reload --port 8000")
else:
    print("\nPLEASE FIX THE ISSUES ABOVE BEFORE STARTING THE SERVER")
    sys.exit(1)

print("="*60)
