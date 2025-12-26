# Quick Start Guide

Get the LLM Financial Chatbot running in 5 minutes.

## 1. Setup Environment (2 min)

```bash
# Navigate to project
cd llm-fin-chatbot

# Activate virtual environment
venv\Scripts\activate    # Windows
source venv/bin/activate # macOS/Linux

# Install dependencies (if not already done)
pip install -r requirements.txt
```

## 2. Configure API Keys (1 min)

```bash
# Copy template
copy .env.template .env    # Windows
cp .env.template .env      # macOS/Linux
```

**Edit `.env` and add at least one API key:**

```env
DEEPSEEK_API_KEY=sk-your-deepseek-key-here
# OR
OPENAI_API_KEY=sk-your-openai-key-here
# OR leave both empty for Demo mode
```

## 3. Start Server (1 min)

```bash
uvicorn src.server:app --reload --port 8000
```

**Expected output:**
```
Starting Robo-Advisor LLM Server
============================================================
DeepSeek API Key present: True
OpenAI API Key present: False
Hallucination threshold: 1.0
Debug mode: False
============================================================
✓ MCEncoder available for semantic-entropy
============================================================
INFO:     Uvicorn running on http://0.0.0.0:8000
```

## 4. Test API (1 min)

**Open new terminal and test:**

**PowerShell:**
```powershell
Invoke-RestMethod -Uri http://localhost:8000/health
```

**Bash:**
```bash
curl http://localhost:8000/health
```

**Expected response:**
```json
{
  "status": "ok",
  "deepseek": true,
  "openai": false,
  "nli_loaded": true,
  "entropy_enabled": true,
  "debug": false
}
```

## 5. Launch UI (optional)

**In another terminal:**
```bash
streamlit run src/demo_streamlit.py
```

Browser opens at `http://localhost:8501` with the web interface.

## Common Commands

### Run Tests
```bash
python scripts/test_server_requests.py
```

### Test Question (PowerShell)
```powershell
$body = @{
    text = "What is portfolio diversification?"
    provider = "auto"
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/ask -Method Post -Body $body -ContentType "application/json"
```

### Test Question (Bash)
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"text":"What is portfolio diversification?","provider":"auto"}'
```

### Enable Debug Mode
```env
# In .env file
DEBUG=1
```

Then restart server.

## Troubleshooting

### "Server not running"
- Check if port 8000 is available
- Look for error messages in terminal
- Try `pip install python-dotenv`

### "No API key configured"
- Ensure `.env` file exists
- Check API key is set correctly
- Restart server after editing `.env`

### "No passages found"
- Ensure `data/passages.txt` exists
- Check file has content (passages separated by blank lines)
- Use "Rebuild Index" button in UI

### "Module not found"
- Install missing package: `pip install <package>`
- Check virtual environment is activated

## Next Steps

1. **Add your data:** Edit `data/passages.txt` with financial knowledge
2. **Rebuild index:** Use UI button or run:
   ```bash
   python -c "from src.retrieval import rebuild_tfidf_index; rebuild_tfidf_index()"
   ```
3. **Configure threshold:** Adjust `HALLU_THRESHOLD` in `.env`
4. **Test thoroughly:** Run `python scripts/test_server_requests.py`

## Quick Reference

| Task | Command |
|------|---------|
| Start server | `uvicorn src.server:app --reload --port 8000` |
| Start UI | `streamlit run src/demo_streamlit.py` |
| Run tests | `python scripts/test_server_requests.py` |
| Health check | `curl http://localhost:8000/health` |
| Enable debug | Set `DEBUG=1` in `.env` |

For full documentation, see [README.md](README.md).
