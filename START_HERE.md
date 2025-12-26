# START HERE - Complete Setup Guide

## ✅ All Checks Passed!

Your system is ready to run. Follow these steps **in order**:

---

## Step 1: Run Setup Check (DONE ✓)

You've already run this, but for future reference:

```bash
python scripts/check_setup.py
```

---

## Step 2: Start the Server

**Open a terminal in the project directory and run:**

```bash
uvicorn src.server:app --reload --port 8000
```

**Expected output:**
```
============================================================
Starting Robo-Advisor LLM Server
============================================================
DeepSeek API Key present: True
OpenAI API Key present: False
DeepSeek URL: https://api.deepseek.com/v1/chat/completions
Hallucination threshold: 1.0
Debug mode: False
============================================================
✗ No NLI loader found; skipping NLI initialization
✗ No MCEncoder available; semantic-entropy disabled
============================================================
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

**⚠️ Note:** Hallucination detection is temporarily disabled to prevent startup hangs. See "Enable Advanced Features" section below.

**Keep this terminal open! The server must stay running.**

---

## Step 3: Test the Server

**Open a NEW terminal (keep server running in the first one) and run:**

```bash
python scripts/test_server_requests.py
```

**Expected:**
```
============================================================
Test 1: Health Check
✓ Health endpoint returned status: ok
  - DeepSeek configured: True
  - OpenAI configured: False
...
Results: 3/3 tests passed
🎉 All tests passed!
```

---

## Step 4: Launch Web UI (Optional)

**In the same second terminal, run:**

```bash
cd frontend
npm install  # First time only
npm start
```

Browser will open at `http://localhost:3000`

**Now you can:**
1. Chat with the AI assistant in a modern interface
2. Ask questions like "What was our Q3 performance vs the S&P 500?"
3. Get real answers from DeepSeek using your knowledge base!
4. Manage portfolios and view risk assessments

---

## Quick Test

**PowerShell (in your second terminal):**
```powershell
$body = @{
    text = "What is portfolio diversification?"
    provider = "auto"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/ask -Method Post -Body $body -ContentType "application/json"
```

**You should get a JSON response with:**
- `answer`: Real answer from DeepSeek
- `passages_used`: 2-3 passages
- `is_hallucination`: null (temporarily disabled)
- `_meta.provider`: "deepseek"

---

## Troubleshooting

### Server won't start

**Check the error message:**

1. **"Address already in use"** → Port 8000 is busy
   ```bash
   # Use different port:
   uvicorn src.server:app --reload --port 8001
   ```

2. **"ModuleNotFoundError"** → Missing package
   ```bash
   pip install <missing-package>
   ```

3. **Hangs/freezes** → Server is stuck
   - Press Ctrl+C to stop
   - Re-run: `python scripts/check_setup.py`

### UI can't connect to backend

**This means the frontend can't reach the server:**

1. **Check server is running** in first terminal
2. **Check server is on port 8000** (look for "running on http://127.0.0.1:8000")
3. **Refresh the browser page**

### "502 Bad Gateway"

**Server is crashing on requests:**

1. Look at server terminal for error messages
2. Common issue: Missing packages
   ```bash
   pip install -r requirements.txt
   ```

---

## Enable Advanced Features (Optional)

### Hallucination Detection (semantic entropy)

Currently disabled to prevent startup hangs. To enable:

1. **Ensure sentence-transformers model is downloaded:**
   ```bash
   python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"
   ```

2. **Edit [src/server.py:43-44](src/server.py:43-44)** and uncomment the MCEncoder import

3. **Edit [src/server.py:87](src/server.py:87)** and change:
   ```python
   mc = None  # Disabled for now
   ```
   to:
   ```python
   mc = MCEncoder() if MCEncoder is not None else None
   ```

4. Restart server

### NLI Contradiction Detection

Currently disabled. To enable:

1. **Download NLI model:**
   ```bash
   python -c "from transformers import AutoTokenizer, AutoModelForSequenceClassification; model = AutoModelForSequenceClassification.from_pretrained('cross-encoder/nli-deberta-v3-base'); tokenizer = AutoTokenizer.from_pretrained('cross-encoder/nli-deberta-v3-base'); model.save_pretrained('models/nli'); tokenizer.save_pretrained('models/nli')"
   ```

2. **Edit [src/server.py:61-62](src/server.py:61-62)** and uncomment the load_model import

3. Restart server

---

## What's Working Now

✅ **FastAPI server** - Runs on port 8000
✅ **DeepSeek API** - Primary LLM provider
✅ **OpenAI fallback** - If DeepSeek unavailable
✅ **Demo mode** - Works without API keys
✅ **TF-IDF retrieval** - Knowledge base search
✅ **Provider selection** - Choose LLM in UI
✅ **React Frontend** - Modern web interface
✅ **Error handling** - Robust fallbacks

⚠️ **Temporarily Disabled:**
❌ Hallucination detection (entropy, is_hallucination will be null)
❌ NLI contradiction scoring (contradiction_score will be null)

**Everything else works perfectly!**

---

## Summary

**To run the system:**

```bash
# Terminal 1: Start server
uvicorn src.server:app --reload --port 8000

# Terminal 2: Test it
python scripts/test_server_requests.py

# Terminal 2: Launch UI (optional)
cd frontend
npm start
```

**That's it! 🚀**

---

## Need Help?

1. Check server logs in Terminal 1
2. Run: `python scripts/check_setup.py`
3. Check this guide's troubleshooting section
4. Review [README.md](README.md) for full documentation

