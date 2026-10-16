import torch
import numpy as np
from transformers import AutoModel, AutoTokenizer
import torch.nn.functional as F

MODEL = "sentence-transformers/all-MiniLM-L6-v2"

class MCEncoder:
    def __init__(self, model_name=MODEL, device=None):
        import os
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name).to(self.device)

    def embed(self, texts, mc_rounds=8):
        self.model.train()  # enable dropout
        embeddings = []
        with torch.no_grad():
            for _ in range(mc_rounds):
                encoded = self.tokenizer(texts, padding=True, truncation=True, return_tensors="pt").to(self.device)
                out = self.model(**encoded, return_dict=True)
                hidden = out.last_hidden_state
                attn_mask = encoded["attention_mask"].unsqueeze(-1)
                summed = (hidden * attn_mask).sum(1)
                counts = attn_mask.sum(1)
                emb = (summed / counts).cpu().numpy()
                embeddings.append(emb)
        embeddings = np.stack(embeddings, axis=1)
        return embeddings

def semantic_entropy_from_embeddings(embs, temp=0.1):
    import math, torch
    batch, mc, dim = embs.shape
    ent = []
    for i in range(batch):
        vecs = embs[i]
        mean_vec = vecs.mean(axis=0)
        sims = (vecs @ mean_vec) / (np.linalg.norm(vecs, axis=1) * np.linalg.norm(mean_vec) + 1e-8)
        probs = F.softmax(torch.tensor(sims / temp), dim=0).numpy()
        entropy = -np.sum(probs * np.log(probs + 1e-12))
        ent.append(float(entropy))
    return np.array(ent)

if __name__ == "__main__":
    enc = MCEncoder()
    texts = ["Our portfolio returned 5% last quarter.", "The market closed at 1000 points."]
    embs = enc.embed(texts, mc_rounds=8)
    entropies = semantic_entropy_from_embeddings(embs)
    print("Entropies:", entropies)
