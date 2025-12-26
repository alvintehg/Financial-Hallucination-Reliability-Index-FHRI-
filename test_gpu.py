import torch
from transformers import AutoModel

print("Testing GPU availability...")
print(f"CUDA available: {torch.cuda.is_available()}")
print(f"GPU device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'N/A'}")

if torch.cuda.is_available():
    print("\nTesting model loading on GPU...")
    try:
        model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2').to('cuda')
        print("[OK] Model loaded on GPU successfully!")
        print(f"Model device: {next(model.parameters()).device}")
        print("\n[SUCCESS] GPU is ready to use!")
    except Exception as e:
        print(f"[ERROR] Error loading model on GPU: {e}")
else:
    print("[ERROR] CUDA not available")

