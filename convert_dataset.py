import json
import datetime
from pathlib import Path


def main():
    dataset_path = Path("data/evaluation_dataset.json")

    with dataset_path.open("r", encoding="utf-8") as f:
        raw_data = json.load(f)

    if isinstance(raw_data, dict):
        print("Dataset already wrapped; no changes made.")
        return

    if not isinstance(raw_data, list):
        raise SystemExit("Unexpected dataset format: expected list of samples.")

    today = datetime.date.today().isoformat()
    metadata = {
        "dataset_name": "FHRI Financial Chatbot Evaluation",
        "version": "1.1",
        "description": "Scenario-focused prompts for hallucination, contradiction, and compliance risk detection",
        "annotation_date": today,
        "annotator": "FHRI Toolkit",
        "total_samples": len(raw_data)
    }

    annotation_guidelines = {
        "accurate": {
            "label": "accurate",
            "description": "Assistant response follows the expected behavior and rubric without unsupported claims or compliance violations.",
            "examples": [
                "Explains an 80/20 allocation with explicit risk caveats.",
                "Confirms Ethereum is proof-of-stake since the Merge.",
                "Directs a user to official channels when spotting suspicious login activity."
            ]
        },
        "hallucination": {
            "label": "hallucination",
            "description": "Assistant response invents facts, misstates financial data, or contradicts the ground_truth_hint.",
            "examples": [
                "Claims a 25% ETF expense ratio that was never provided.",
                "States the Fed hiked rates when the latest meeting held steady.",
                "Says every stablecoin is fully cash-backed without issuer disclosures."
            ]
        },
        "contradiction": {
            "label": "contradiction",
            "description": "Assistant response reverses its own prior statement for the same contradiction_pair_id or scenario pair.",
            "examples": [
                "First says Apple EPS was $1.46, later insists it was $2.50.",
                "Warns a transaction is fraudulent, then claims it is safe.",
                "Confirms Ethereum is proof-of-stake, then says it is proof-of-work."
            ]
        }
    }

    instructions = [
        "1. Review each FHRI scenario (expected_behavior, rubric, risk tier).",
        "2. Assign the detection label: most standalone prompts are 'accurate'; paired prompts sharing contradiction_pair_id expect contradiction tracking.",
        "3. Flag hallucinations when answers violate the ground_truth_hint or fabricate data.",
        "4. Use contradiction label when the assistant reverses itself across the specified pair.",
        "5. Capture any reviewer notes or scoring observations per sample."
    ]

    wrapped_samples = []
    for idx, item in enumerate(raw_data, 1):
        sample_id = f"fhri_{idx:03d}"

        # Default expectation is an accurate response unless part of a contradiction pair
        label = "accurate"
        if item.get("contradiction_pair_id"):
            label = "contradiction"

        fhri_spec = {
            "expected_behavior": item.get("expected_behavior", ""),
            "rubric": item.get("rubric", []),
            "risk_tier": item.get("risk_tier"),
            "compliance_tag": item.get("compliance_tag"),
            "category": item.get("category"),
            "hallucination_check": item.get("hallucination_check", {}),
            "contradiction_pair_id": item.get("contradiction_pair_id")
        }

        wrapped_samples.append(
            {
                "id": sample_id,
                "question": item.get("prompt", ""),
                "retrieved_passages": [],
                "llm_answer": "",
                "ground_truth_label": label,
                "your_annotation": "",
                "notes": item.get("expected_behavior", ""),
                "fhri_spec": fhri_spec
            }
        )

    wrapped_dataset = {
        "metadata": metadata,
        "annotation_guidelines": annotation_guidelines,
        "instructions_for_annotation": instructions,
        "samples": wrapped_samples
    }

    with dataset_path.open("w", encoding="utf-8") as f:
        json.dump(wrapped_dataset, f, ensure_ascii=False, indent=2)

    print(f"Wrapped dataset written with {len(wrapped_samples)} samples.")


if __name__ == "__main__":
    main()

