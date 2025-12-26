"""Check if backend models are using GPU"""
import requests
import json

# Test if models load on GPU
print("Testing GPU usage in backend models...")
print("=" * 60)

# Test 1: Check if CUDA is available
try:
    import torch
    print(f"CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU device: {torch.cuda.get_device_name(0)}")
except:
    print("Could not check CUDA")

print("\n" + "=" * 60)
print("Testing model initialization...")

# Test 2: Initialize entropy model and check device
try:
    from src.hallucination_entropy import MCEncoder
    encoder = MCEncoder()
    print(f"Entropy model device: {encoder.device}")
    if encoder.device == "cuda":
        print("[OK] Entropy model will use GPU")
    else:
        print("[WARNING] Entropy model will use CPU")
except Exception as e:
    print(f"[ERROR] Could not test entropy model: {e}")

# Test 3: Initialize NLI model and check device
try:
    from src.nli_infer import load_model
    tokenizer, model = load_model()
    model_device = next(model.parameters()).device
    print(f"NLI model device: {model_device}")
    if "cuda" in str(model_device):
        print("[OK] NLI model will use GPU")
    else:
        print("[WARNING] NLI model will use CPU")
except Exception as e:
    print(f"[ERROR] Could not test NLI model: {e}")

print("\n" + "=" * 60)
print("Summary:")
print("- Models are configured to use GPU if CUDA is available")
print("- They will automatically use GPU when loaded during evaluation")
print("- Check Task Manager GPU usage during evaluation to confirm")

















