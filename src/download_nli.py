# src/download_nli.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification
MODEL_ID = "roberta-large-mnli"   # smaller option: "distilroberta-base"
OUTDIR = "models/nli"

print("Downloading tokenizer and model:", MODEL_ID)
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
print("Saving to:", OUTDIR)
tokenizer.save_pretrained(OUTDIR)
# Disable safetensors to avoid Windows file-lock issues during save
model.save_pretrained(OUTDIR, safe_serialization=False)
print("Done.")
#setx OPENAI_API_KEY "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"
#$env:OPENAI_API_KEY="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"
#$env:FINNHUB_API_KEY="d28sl21r01qle9gskpk0d28sl21r01qle9gskpkg"
#deepseek $env:DEESEEK_API_KEY="sk-0ea9b9a48e404132855fbf3cfb5ac41a"
#.\venv\Scripts\Activate.ps1
#streamlit run src/demo_streamlit.py
