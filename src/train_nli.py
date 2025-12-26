from datasets import Dataset
import pandas as pd
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer

MODEL = "roberta-large-mnli"

def load_my_data(csv_path):
    df = pd.read_csv(csv_path)
    return Dataset.from_pandas(df)

def preprocess(examples, tokenizer):
    return tokenizer(examples["premise"], examples["hypothesis"], truncation=True, padding="max_length", max_length=256)

def train(csv_path="data/nli_finance.csv", out_dir="models/nli"):
    ds = load_my_data(csv_path)
    ds = ds.train_test_split(test_size=0.1)
    tokenizer = AutoTokenizer.from_pretrained(MODEL)
    ds = ds.map(lambda x: preprocess(x, tokenizer), batched=True)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=3)
    args = TrainingArguments(output_dir=out_dir, per_device_train_batch_size=2, num_train_epochs=1, evaluation_strategy="epoch", save_total_limit=1)
    trainer = Trainer(model=model, args=args, train_dataset=ds["train"], eval_dataset=ds["test"], tokenizer=tokenizer)
    trainer.train()
    trainer.save_model(out_dir)

if __name__ == "__main__":
    train()
