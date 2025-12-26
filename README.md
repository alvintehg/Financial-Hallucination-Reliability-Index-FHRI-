# LLM Financial Chatbot with Hallucination Detection

A production-ready LLM-powered robo-advisor prototype with semantic-entropy hallucination detection, NLI-based contradiction scoring, and RAG (Retrieval-Augmented Generation) grounding.

## Features

- **🤖 Multi-Provider LLM Support**: DeepSeek (primary), OpenAI (fallback), or Demo mode
- **🔍 RAG-Based Grounding**: TF-IDF or FAISS vector retrieval for factual accuracy
- **🎯 Hallucination Detection**: Monte Carlo Dropout-based semantic entropy
- **⚖️ Contradiction Scoring**: Optional NLI-based consistency checking
- **🌐 Modern Web UI**: React frontend with real-time analytics
- **🔄 Robust API**: FastAPI server with retries, timeout, and error handling
- **📊 Comprehensive Logging**: Debug mode for detailed diagnostics

## Project Structure

```
llm-fin-chatbot/
├── src/
│   ├── server.py               # FastAPI server with DeepSeek/OpenAI integration
│   ├── retrieval.py            # TF-IDF and FAISS retrieval module
│   ├── hallucination_entropy.py # Monte Carlo dropout for hallucination detection
│   └── nli_infer.py            # NLI-based contradiction scoring (optional)
├── frontend/
│   ├── src/                    # React components and pages
│   ├── public/                 # Static assets
│   └── package.json            # Node.js dependencies
├── data/
│   ├── passages.txt            # Knowledge base (passages separated by blank lines)
│   └── trusted_docs/           # Finnhub-fetched documents (optional)
├── models/                     # Saved TF-IDF/FAISS indices and NLI models
├── scripts/
│   ├── test_server_requests.py      # Automated API tests
│   ├── evaluate_detection.py        # Hallucination/contradiction detection evaluation
│   ├── measure_latency.py           # Latency measurement and analysis
│   ├── generate_contradictions.py   # Synthetic contradiction pair generator
│   └── generate_plots.py            # Visualization script for results
├── docs/
│   └── user_study_template.md       # User study questionnaire template
├── results/                          # Evaluation results and plots (generated)
├── requirements.txt                  # Python dependencies
├── .env.template                     # Environment variable template
└── README.md                         # This file
```

## Quick Start

### 1. Prerequisites

- Python 3.8+
- Virtual environment (recommended)
- API key for DeepSeek or OpenAI

### 2. Installation

```bash
# Clone or download the repository
cd llm-fin-chatbot

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

```bash
# Copy the template
copy .env.template .env    # Windows
cp .env.template .env      # macOS/Linux

# Edit .env and add your API keys
```

**Required variables:**

```env
# Primary: DeepSeek (recommended)
DEEPSEEK_API_KEY=your_deepseek_key_here
DEEPSEEK_URL=https://api.deepseek.com/v1/chat/completions

# Fallback: OpenAI (optional)
OPENAI_API_KEY=your_openai_key_here

# Hallucination threshold (higher = stricter)
HALLU_THRESHOLD=1.0

# Debug mode (0 or 1)
DEBUG=0
```

**Provider priority:**
1. If `DEEPSEEK_API_KEY` is set → uses DeepSeek
2. Else if `OPENAI_API_KEY` is set → uses OpenAI
3. Else → Demo mode (placeholder responses)

### 4. Prepare Knowledge Base

Create or edit `data/passages.txt` with your financial knowledge base:

```txt
Apple Inc. (AAPL) reported Q1 2024 revenue of $119.6 billion, up 2% YoY. iPhone sales reached $69.7 billion. Services revenue was $23.1 billion, a new record.

Microsoft Corporation (MSFT) fiscal Q2 2024 revenue was $62 billion, up 18% YoY. Cloud revenue (Azure) grew 30%. Intelligent Cloud segment revenue was $25.9 billion.

Portfolio diversification is a risk management strategy that mixes a wide variety of investments within a portfolio. The rationale is that a portfolio constructed of different kinds of assets will, on average, yield higher returns and pose a lower risk than any individual investment found within the portfolio.
```

**Format:** Passages separated by blank lines (double newline).

### 5. Run the Server

```bash
# Start FastAPI server
uvicorn src.server:app --reload --port 8000

# Server will be available at http://localhost:8000
# API docs: http://localhost:8000/docs
```

### 6. Run the React Frontend

```bash
# In a separate terminal
cd frontend
npm install  # First time only
npm start

# UI will open at http://localhost:3000
```

## Usage

### API Endpoints

#### Health Check

```bash
curl http://localhost:8000/health
```

Response:
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

#### Ask Question

**PowerShell:**
```powershell
$body = @{
    text = "What was Apple's revenue last quarter?"
    provider = "auto"
    k = 5
} | ConvertTo-Json

Invoke-RestMethod -Uri http://localhost:8000/ask -Method Post -Body $body -ContentType "application/json"
```

**Bash/curl:**
```bash
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{
    "text": "What was Apple revenue last quarter?",
    "provider": "auto",
    "k": 5
  }'
```

**Python:**
```python
import requests

response = requests.post(
    "http://localhost:8000/ask",
    json={
        "text": "What is portfolio diversification?",
        "provider": "auto",
        "k": 5
    }
)
print(response.json())
```

**Request parameters:**
- `text` (required): User question
- `provider` (optional): `"auto"`, `"deepseek"`, `"openai"`, or `"demo"` (default: `"auto"`)
- `k` (optional): Number of passages to retrieve (default: `5`)
- `prev_assistant_turn` (optional): Previous answer for contradiction scoring

**Response:**
```json
{
  "answer": "Apple Inc. reported Q1 2024 revenue of $119.6 billion...",
  "entropy": 0.234,
  "is_hallucination": false,
  "contradiction_score": null,
  "passages_used": 3,
  "passages": ["Apple Inc. (AAPL) reported...", "..."],
  "_meta": {
    "provider": "deepseek",
    "latency_s": 1.23,
    "k": 5,
    "retrieval_count": 3
  }
}
```

### React Frontend Features

1. **Modern UI**: Clean, responsive interface built with React and TailwindCSS
2. **Real-time Chat**: Interactive conversation with the AI assistant
3. **Confidence Indicators**: Visual feedback on answer reliability
4. **Portfolio Management**: Track and analyze investment portfolios
5. **Real-time Data**: Live market data integration from Finnhub
6. **Risk Assessment**: FHRI (Financial Health Risk Index) scoring
7. **Responsive Design**: Works seamlessly on desktop and mobile devices

## Testing

### Automated Tests

```bash
# Ensure server is running first
uvicorn src.server:app --port 8000

# In another terminal, run tests
python scripts/test_server_requests.py
```

Expected output:
```
============================================================
LLM Server Test Suite
============================================================
Target: http://localhost:8000
============================================================
Test 1: Health Check
✓ Health endpoint returned status: ok
...
============================================================
TEST SUMMARY
============================================================
✓ PASS: Health Check
✓ PASS: Ask Endpoint (Basic)
✓ PASS: Provider Selection
============================================================
Results: 3/3 tests passed
============================================================

🎉 All tests passed!
```

### Manual Testing

Test different providers:

```bash
# Test DeepSeek
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"text":"What is diversification?","provider":"deepseek"}'

# Test OpenAI
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"text":"What is diversification?","provider":"openai"}'

# Test Demo mode
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" -d '{"text":"What is diversification?","provider":"demo"}'
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DEEPSEEK_API_KEY` | No* | - | DeepSeek API key (primary provider) |
| `DEEPSEEK_URL` | No | `https://api.deepseek.com/v1/chat/completions` | DeepSeek API endpoint |
| `OPENAI_API_KEY` | No* | - | OpenAI API key (fallback provider) |
| `HALLU_THRESHOLD` | No | `1.0` | Entropy threshold for hallucination detection |
| `DEBUG` | No | `0` | Enable debug logging (`1` = on, `0` = off) |
| `FINNHUB_API_KEY` | No | - | Finnhub API key for data ingestion (UI only) |

\* At least one of `DEEPSEEK_API_KEY` or `OPENAI_API_KEY` recommended. Otherwise, demo mode is used.

### Hallucination Detection

The `HALLU_THRESHOLD` controls sensitivity:
- **Lower values (0.5-1.0)**: More sensitive, may flag uncertain answers
- **Higher values (1.5-2.5)**: Less sensitive, only flags obvious hallucinations
- **Default (1.0)**: Balanced setting

Entropy is computed using Monte Carlo Dropout with 6 stochastic forward passes.

### Debug Mode

Set `DEBUG=1` to enable:
- Detailed request/response logging
- Full LLM provider responses in API output
- Passage content logging
- Error stack traces

⚠️ **Warning:** Debug mode may log sensitive data. Use only in development.

## Architecture

### LLM Provider Selection

```
User Request
     ↓
Provider specified?
     ↓
   [Auto]────────────[Specific Provider]
     ↓                      ↓
DEEPSEEK_API_KEY set?    Force provider
     ↓                      ↓
  [Yes]──[No]          Call provider
     ↓      ↓               ↓
DeepSeek   ↓            Return
     ↓   OPENAI_API_KEY set?
     ↓      ↓
     ↓   [Yes]──[No]
     ↓      ↓      ↓
     ↓   OpenAI  Demo
     ↓      ↓      ↓
     └──────┴──────┘
            ↓
       Return answer
```

### Request Flow

```
1. User Question
   ↓
2. Retrieve relevant passages (TF-IDF/FAISS)
   ↓
3. Build grounded prompt with context
   ↓
4. Call LLM (DeepSeek/OpenAI/Demo)
   ↓
5. Compute semantic entropy (hallucination score)
   ↓
6. Optional: NLI contradiction scoring
   ↓
7. Return structured response
```

## Troubleshooting

### Server won't start

**Issue:** `ModuleNotFoundError: No module named 'dotenv'`

**Solution:**
```bash
pip install python-dotenv
```

---

**Issue:** `ImportError: cannot import name 'MCEncoder'`

**Solution:** MCEncoder is optional. Server will run without it, but entropy detection will be disabled.

---

### Retrieval issues

**Issue:** `No passages found` or `TF-IDF index not found`

**Solution:**
1. Ensure `data/passages.txt` exists and has content
2. Rebuild index:
   ```bash
   python -c "from src.retrieval import rebuild_tfidf_index; rebuild_tfidf_index()"
   ```

---

### API errors

**Issue:** `DeepSeek API timeout` or `502 Bad Gateway`

**Solution:**
- Check internet connection
- Verify API key is correct
- Try fallback: set `OPENAI_API_KEY` as backup
- Or use demo mode: send `{"provider": "demo"}` in request

---

**Issue:** `400 Bad Request: DeepSeek API key not configured`

**Solution:**
- Add `DEEPSEEK_API_KEY` to `.env` file
- Restart server after updating `.env`
- Or specify different provider: `{"provider": "openai"}` or `{"provider": "demo"}`

## Evaluation and Testing

This project includes comprehensive evaluation tools for measuring system performance. This section is particularly useful for FYP (Final Year Project) students who need to document results.

### 1. Hallucination Detection Evaluation

Measure precision, recall, and F1-score for hallucination detection.

**Step 1: Create Annotated Dataset**

```bash
# Copy the template
copy data\evaluation_template.json data\evaluation_dataset.json

# Edit evaluation_dataset.json and add your annotated samples
# You need 50-100 Q&A pairs labeled as "accurate" or "hallucination"
```

**Step 2: Run Evaluation**

```bash
# Ensure server is running first
uvicorn src.server:app --port 8000

# In another terminal, run evaluation
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/evaluation_report.json
```

**Expected Output:**
- Precision, Recall, F1-score for each class (hallucination, accurate, contradiction)
- Confusion matrix
- Overall accuracy and macro F1
- Detailed results saved to JSON

### 2. Latency Measurement

Measure response time statistics (mean, p95, p99).

```bash
# Ensure server is running
uvicorn src.server:app --port 8000

# Run latency tests (10 runs per question)
python scripts/measure_latency.py --runs 10 --output results/latency_report.json

# For more extensive testing
python scripts/measure_latency.py --runs 50 --k 5 --provider auto
```

**Output Metrics:**
- Mean, median, min, max latency
- p50, p95, p99 percentiles
- Success rate
- Backend vs. network latency breakdown

### 3. Generate Visualization Plots

Create plots for your FYP report.

```bash
# Install plotting dependencies first
pip install matplotlib seaborn

# Generate all plots
python scripts/generate_plots.py --evaluation results/evaluation_report.json --latency results/latency_report.json --output results/plots/
```

**Generated Plots:**
- Confusion matrix (heatmap)
- Precision/Recall/F1 comparison (bar chart)
- Latency distribution (histogram)
- Latency percentiles (bar chart)
- Success rate (pie chart)

### 4. Generate Synthetic Contradiction Pairs

Test NLI contradiction detection with synthetic data.

```bash
# Generate 50 contradiction pairs
python scripts/generate_contradictions.py --output data/contradiction_pairs.json --count 50
```

This creates finance-specific contradiction pairs like:
- Revenue contradictions: "$85B" vs. "$95B"
- Performance contradictions: "outperformed" vs. "underperformed"
- Sector contradictions: "energy returned 1.8%" vs. "energy declined 2.5%"

### 5. User Study

Conduct a user study to measure trust and satisfaction.

**Template:** See [docs/user_study_template.md](docs/user_study_template.md)

**Steps:**
1. Recruit 5-10 participants (students, early career professionals)
2. Have them complete 5 task scenarios (10 minutes)
3. Collect questionnaire responses (5 minutes)
4. Analyze trust scores, satisfaction scores, and qualitative feedback

**Key Metrics to Report:**
- Mean trust score (Q1-Q7 from questionnaire)
- Mean satisfaction score (Q8-Q12)
- % of users who noticed hallucination detection
- Comparative trust: with vs. without detection features

### Evaluation Checklist for FYP

✅ **What You Can Do in VS Code:**
- [x] Create evaluation dataset template
- [x] Create evaluation scripts (detection, latency, plotting)
- [x] Generate synthetic contradiction pairs
- [x] Create user study questionnaire template
- [ ] Run evaluation scripts and collect results
- [ ] Generate plots for report

⚠️ **What You Must Do Outside VS Code:**
- [ ] Manually annotate 50-100 Q&A pairs as accurate/hallucination
- [ ] Conduct user study with 5-10 participants
- [ ] Analyze survey responses
- [ ] Write FYP report sections (Evaluation, Results, Discussion)
- [ ] Create presentation slides

### Example Evaluation Workflow

```bash
# 1. Generate synthetic test data
python scripts/generate_contradictions.py --output data/contradiction_pairs.json --count 50

# 2. Measure latency (50 runs)
python scripts/measure_latency.py --runs 50 --output results/latency_report.json

# 3. Evaluate detection (after manual annotation)
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/evaluation_report.json

# 4. Generate plots for report
python scripts/generate_plots.py --evaluation results/evaluation_report.json --latency results/latency_report.json --output results/plots/

# 5. View results
# Check results/evaluation_report.json for metrics
# Check results/plots/ for visualizations
```

### Expected Results Table (Example)

| Metric | Hallucination Detection | Contradiction Detection | Latency |
|--------|------------------------|------------------------|---------|
| Precision | 0.85 | 0.78 | N/A |
| Recall | 0.82 | 0.75 | N/A |
| F1-Score | 0.83 | 0.76 | N/A |
| Mean Latency | N/A | N/A | 1,234ms |
| P95 Latency | N/A | N/A | 2,100ms |
| Success Rate | N/A | N/A | 98.5% |

*(Fill in actual values after running evaluation)*

---

## Advanced Usage

### Building FAISS Index (Optional)

For better retrieval with semantic search:

```python
from src.retrieval import build_faiss_index

build_faiss_index(
    passages_file="data/passages.txt",
    embed_model="sentence-transformers/all-MiniLM-L6-v2"
)
```

Requires: `sentence-transformers`, `faiss-cpu` (already in requirements.txt)

### NLI Contradiction Detection (Optional)

1. Download NLI model to `models/nli/`:
   ```python
   from transformers import AutoTokenizer, AutoModelForSequenceClassification

   model = AutoModelForSequenceClassification.from_pretrained("cross-encoder/nli-deberta-v3-base")
   tokenizer = AutoTokenizer.from_pretrained("cross-encoder/nli-deberta-v3-base")

   model.save_pretrained("models/nli")
   tokenizer.save_pretrained("models/nli")
   ```

2. Server will auto-load on startup

3. Use `prev_assistant_turn` in requests:
   ```json
   {
     "text": "What about Q2?",
     "prev_assistant_turn": "Apple Q1 revenue was $119B",
     "provider": "auto"
   }
   ```

### Custom DeepSeek Endpoint

If using a custom DeepSeek-compatible endpoint:

```env
DEEPSEEK_URL=https://your-custom-endpoint.com/v1/chat/completions
DEEPSEEK_API_KEY=your_custom_key
```

## Dependencies

Backend (Python):
- `fastapi` - API server
- `uvicorn` - ASGI server
- `python-dotenv` - Environment variables
- `requests` - HTTP client
- `scikit-learn` - TF-IDF retrieval

Frontend (Node.js):
- `react` - UI framework
- `react-router-dom` - Client-side routing
- `axios` - HTTP client
- `tailwindcss` - CSS framework
- `recharts` - Data visualization

ML (optional but recommended):
- `torch` - Neural network backend
- `transformers` - NLP models
- `sentence-transformers` - Embeddings
- `faiss-cpu` - Vector search

See [requirements.txt](requirements.txt) for full list.

## Performance Tips

1. **Use FAISS**: For >1000 passages, FAISS is faster than TF-IDF
2. **Reduce k**: Lower `k` (e.g., 3) for faster retrieval
3. **Disable entropy**: Comment out MCEncoder init if not needed
4. **Cache passages**: TF-IDF/FAISS artifacts are cached in `models/`
5. **Use GPU**: Install `torch` with CUDA for faster hallucination detection

## Security Notes

- **Never commit `.env`**: API keys should remain secret
- **Use HTTPS**: In production, deploy behind HTTPS reverse proxy
- **Validate inputs**: FastAPI handles basic validation
- **Rate limiting**: Consider adding rate limits for production
- **Debug mode**: Disable `DEBUG=1` in production (logs may contain sensitive data)

## License

This is a prototype for educational and research purposes.

## References

Inspired by:
- [TradingAgents-CN](https://github.com/hsliuping/TradingAgents-CN) - Multi-agent trading system structure
- Semantic Entropy for hallucination detection (Farquhar et al.)
- RAG (Retrieval-Augmented Generation) for grounding
- NLI-based consistency checking

## Support

For issues or questions:
1. Check [Troubleshooting](#troubleshooting) section
2. Review server logs (especially with `DEBUG=1`)
3. Test with `scripts/test_server_requests.py`
4. Verify `.env` configuration

---

**Built with DeepSeek integration, robust error handling, and production-ready patterns.**
