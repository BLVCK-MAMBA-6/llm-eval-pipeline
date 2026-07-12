import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-0.5B"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32)
model.eval()


def generate(prompt, max_new_tokens=40):
    """Simple KV-cached generation -- reused from the inference server project."""
    input_ids = tokenizer(prompt, return_tensors="pt")["input_ids"]
    past_key_values = None
    current_input = input_ids

    for _ in range(max_new_tokens):
        with torch.no_grad():
            outputs = model(current_input, past_key_values=past_key_values, use_cache=True)
        past_key_values = outputs.past_key_values
        next_token_id = torch.argmax(outputs.logits[0, -1, :]).item()
        if next_token_id == tokenizer.eos_token_id:
            break
        current_input = torch.tensor([[next_token_id]])
        input_ids = torch.cat([input_ids, current_input], dim=1)

    # only decode the NEW tokens, not the prompt, so checks aren't confused
    # by the prompt text also containing the expected answer
    new_tokens = input_ids[0][len(tokenizer(prompt)["input_ids"]):]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)


def check_exact_match(output, expected):
    # normalize: strip whitespace, lowercase, drop trailing punctuation noise
    normalized_output = output.strip().lower().rstrip(".")
    normalized_expected = expected.strip().lower()
    return normalized_output == normalized_expected


def check_contains(output, expected):
    return expected.strip().lower() in output.strip().lower()


def run_rule_based_eval(dataset_path):
    with open(dataset_path) as f:
        dataset = json.load(f)

    results = []
    for case in dataset:
        if case["type"] not in ("exact_match", "contains"):
            continue  # skip judge cases -- that's Stage 2

        output = generate(case["prompt"])

        if case["type"] == "exact_match":
            passed = check_exact_match(output, case["expected"])
        else:  # contains
            passed = check_contains(output, case["expected"])

        results.append({
            "id": case["id"],
            "type": case["type"],
            "prompt": case["prompt"],
            "expected": case["expected"],
            "actual_output": output,
            "passed": passed,
        })

        status = "PASS" if passed else "FAIL"
        print(f"[{status}] {case['id']}: expected '{case['expected']}' -> got '{output.strip()[:60]}'")

    return results


if __name__ == "__main__":
    results = run_rule_based_eval("golden_dataset.json")

    total = len(results)
    passed = sum(r["passed"] for r in results)
    print(f"\n--- Summary ---")
    print(f"Rule-based checks: {passed}/{total} passed")

    with open("results_stage1.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results saved to results_stage1.json")