# FHRI: Finance Hallucination Reliability Index

Code, dataset, and demo app for the **Finance Hallucination Reliability Index (FHRI)**, a scenario-aware composite score for detecting hallucinations and contradictions in LLM-powered financial chatbots.

> 📄 **Paper:** [FHRI: Scenario-Aware Reliability Scoring for Hallucination and Contradiction Detection in Financial LLM Responses](https://ieeexplore.ieee.org/document/11720077)  
> Yi Cheng Teh, Dilshani Mallikarachchi (Xiamen University Malaysia).  
> *2026 IEEE 9th International Conference on Signal and Image Processing Applications (ICSIPA)*, pp. 1–6. DOI: [10.1109/ICSIPA69622.2026.11720077](https://doi.org/10.1109/ICSIPA69622.2026.11720077)

FHRI scores each chatbot answer in `[0, 1]` by combining five reliability signals. Answers that fall below a per-scenario threshold are flagged as likely hallucinations. The repo also contains a full-stack robo-advisor (FastAPI + React) that runs FHRI live on every response.

## How FHRI works

| Component | Signal | Default weight |
|---|---|---|
| **G**: Grounding | Alignment with retrieved passages and live API facts | 0.25 |
| **N/D**: Numeric / Directional | Numeric claims and up/down statements checked against verified market data | 0.25 |
| **T**: Temporal | Whether dates and periods in the answer are valid | 0.20 |
| **C**: Citation | Whether sources are present and credible | 0.15 |
| **E**: Entropy | Inverse semantic entropy from MC-Dropout (`all-MiniLM-L6-v2`) | 0.15 |

- **Scenario-aware weighting**: the query is classified into one of 10 scenarios (`numeric_kpi`, `directional`, `intraday`, `fundamentals`, `regulatory`, `advice`, `multi_ticker`, `news`, `crypto`, `default`), and weights and thresholds change per scenario ([src/scenario_detection.py](src/scenario_detection.py), [src/fhri_scoring.py](src/fhri_scoring.py)).
- **Contradiction detection**: NLI with `cross-encoder/nli-deberta-v3-base` compares an answer against earlier answers ([src/nli_infer.py](src/nli_infer.py)).
- **Renormalization**: if a component can't be computed, the score is calculated over the components that are available.

```
User query ──► Scenario detection ──► Retrieval (TF-IDF / FAISS) + live market data
                                              │
                                              ▼
                                         LLM answer
                                              │
              ┌───────────┬───────────┬───────┴───┬───────────┬───────────┐
              ▼           ▼           ▼           ▼           ▼           ▼
          Grounding   Numeric/Dir  Temporal    Citation    Entropy    NLI contradiction
              └───────────┴───────────┴─────┬─────┴───────────┘           │
                                            ▼                             ▼
                             FHRI (scenario-weighted) ──► reliable / hallucination / contradiction
```

## Dataset

[`data/fhri_evaluation_dataset_full.json`](data/fhri_evaluation_dataset_full.json) contains labelled finance Q&A samples covering all 10 scenarios, with labels split 60% accurate / 20% hallucination / 20% contradiction. Each sample includes the question, the LLM answer, the ground-truth label, and an FHRI spec (expected behaviour, rubric, and risk tier).

| File | Purpose |
|---|---|
| `data/fhri_evaluation_dataset_full.json` | Main evaluation set (multi-scenario) |
| `data/evaluation_dataset.json` | Smaller, manually annotated set |
| `data/contradiction_pairs.json` | Contradiction pairs used for NLI evaluation |
| `data/nli_finance.csv` | Finance NLI premise/hypothesis pairs |
| `data/evaluation_template.json` | Template for annotating new samples |
| `scripts/generate_full_dataset.py`, `data/generate_dataset.py` | Dataset generators |

## Repository layout

```
├── src/                 # Backend: FastAPI server, FHRI scoring, detectors, retrieval, data providers
│   ├── server.py              # API entry point (/ask, /portfolio, /advice, /planning, ...)
│   ├── fhri_scoring.py        # FHRI composite score + scenario weights/thresholds
│   ├── scenario_detection.py  # Query → scenario classifier
│   ├── hallucination_entropy.py  # MC-Dropout semantic entropy
│   ├── nli_infer.py           # NLI contradiction scoring
│   ├── numeric_validators.py, entity_validators.py
│   └── retrieval.py           # TF-IDF / FAISS retrieval
├── scripts/             # Evaluation, threshold sweeps, ablations, baselines, plotting
├── data/                # Evaluation datasets and knowledge-base passages
└── frontend/            # React + Tailwind robo-advisor dashboard
```

## Quick start

### 1. Backend

```bash
python -m venv venv
venv\Scripts\activate            # Windows
# source venv/bin/activate       # macOS / Linux
pip install -r requirements.txt

cp .env.sample .env              # then add your own API keys
uvicorn src.server:app --port 8000
```

At least one LLM key (`DEEPSEEK_API_KEY`, `OPENAI_API_KEY`, or `ANTHROPIC_API_KEY`) is required. Add `FINNHUB_API_KEY` for live market data. See [.env.sample](.env.sample) for every option. Interactive API docs are served at http://localhost:8000/docs.

### 2. Frontend

```bash
cd frontend
npm install
npm start                        # http://localhost:3000
```

The frontend calls the backend at `http://127.0.0.1:8000` ([frontend/src/api.js](frontend/src/api.js)).

### 3. Ask a question

```bash
curl -X POST http://localhost:8000/ask -H "Content-Type: application/json" \
  -d '{"text": "What is Apple'"'"'s current P/E ratio?"}'
```

Each response includes the answer, the FHRI score with its component breakdown, the detected scenario, the entropy value, and the contradiction flags.

## Reproducing the evaluation

With the backend running:

```bash
# FHRI vs entropy-only baseline
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_fhri.json --mode fhri
python scripts/evaluate_detection.py --dataset data/evaluation_dataset.json --output results/eval_baseline.json --mode baseline

# Threshold sweeps (global and per-scenario)
python scripts/run_threshold_sweep.py
python scripts/run_scenario_sweeps.py

# Ablations, comparative baselines, cross-domain, latency
python scripts/evaluate_ablation_study.py
python scripts/evaluate_comparative_baselines.py
python scripts/evaluate_cross_domain.py
python scripts/measure_latency.py --runs 50 --output results/latency_report.json

# Figures
python scripts/plot_confusion_matrix.py
python scripts/plot_scenario_f1_comparison.py
python scripts/plot_fhri_score_distribution.py
```

Run any script with `--help` to see its options. Outputs go to `results/`.

## Robo-advisor features

The demo app wraps FHRI in a full advisory workflow: live portfolio tracking, market overview and sentiment, sector performance, risk-profile questionnaire, allocation and theme recommendations, goal planning, fee-impact analysis, drift alerts, backtesting, ESG scoring, and optional Moomoo brokerage sync.

## Citation

```bibtex
@inproceedings{teh2026fhri,
  title     = {{FHRI}: Scenario-Aware Reliability Scoring for Hallucination and Contradiction Detection in Financial {LLM} Responses},
  author    = {Teh, Yi Cheng and Mallikarachchi, Dilshani},
  booktitle = {2026 IEEE 9th International Conference on Signal and Image Processing Applications (ICSIPA)},
  pages     = {1--6},
  year      = {2026},
  doi       = {10.1109/ICSIPA69622.2026.11720077}
}
```

## Disclaimer

This is a research prototype. It does not provide financial advice.

## License

[MIT](LICENSE)
