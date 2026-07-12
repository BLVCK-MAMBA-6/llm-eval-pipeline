import json
import re
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

MODEL_NAME = "Qwen/Qwen2.5-0.5B"

print("Loading model...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForCausalLM.from_pretrained(MODEL_NAME, dtype=torch.float32)
model.eval()


def generate(prompt, max_new_tokens=60):
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

    new_tokens = input_ids[0][len(tokenizer(prompt)["input_ids"]):]
    return tokenizer.decode(new_tokens, skip_special_tokens=True)

def build_judge_prompt(question, answer, criteria):
    return f"""You are a strict grader. Carefully check the answer against the criteria and real-world facts. Do not assume the answer is correct.

Question: {question}
Answer: {answer}
Criteria: {criteria}

First write a score from 1 to 5 on its own line starting with "SCORE:".
Then write one sentence of reasoning starting with "REASON:".
Do not use angle brackets or placeholders. Only output ONE score and ONE reason.

SCORE:"""


def parse_judge_output(raw_output):
    """
    Extract a score and reason from the judge's raw text.
    Real-world note: this parsing WILL sometimes fail on a small model --
    that failure is itself something we track, not hide.
    """
    score_match = re.search(r"(\d)", raw_output)
    reason_match = re.search(r"REASON:\s*(.+)", raw_output)

    score = int(score_match.group(1)) if score_match else None
    reason = reason_match.group(1).strip() if reason_match else raw_output.strip()[:100]

    return score, reason, (score is not None)


def run_judge_eval(dataset_path):
    with open(dataset_path) as f:
        dataset = json.load(f)

    results = []
    for case in dataset:
        if case["type"] != "judge":
            continue

        # Step 1: system under test answers the question
        answer = generate(case["prompt"], max_new_tokens=60).strip()

        # Step 2: judge grades that answer
        judge_prompt = build_judge_prompt(case["prompt"], answer, case["criteria"])
        raw_judge_output = generate(judge_prompt, max_new_tokens=30)

        # Cut off anything after the first REASON line -- the model
        # sometimes keeps generating additional SCORE/REASON blocks
        # past the first one, which we don't want
        if "REASON:" in raw_judge_output:
            first_reason_idx = raw_judge_output.index("REASON:")
            end_idx = raw_judge_output.find("SCORE:", first_reason_idx)
            if end_idx != -1:
                raw_judge_output = raw_judge_output[:end_idx]

        score, reason, parsed_ok = parse_judge_output(raw_judge_output)
        results.append({
            "id": case["id"],
            "prompt": case["prompt"],
            "answer": answer,
            "criteria": case["criteria"],
            "raw_judge_output": raw_judge_output,
            "score": score,
            "reason": reason,
            "parsed_ok": parsed_ok,
        })

        print(f"\n[{case['id']}]")
        print(f"  Q: {case['prompt']}")
        print(f"  A: {answer[:80]}")
        print(f"  Score: {score} | Reason: {reason}")
        if not parsed_ok:
            print(f"  ⚠️  PARSE FAILED -- raw judge output: {raw_judge_output!r}")

    return results


if __name__ == "__main__":
    results = run_judge_eval("golden_dataset.json")

    parsed_count = sum(r["parsed_ok"] for r in results)
    scored = [r["score"] for r in results if r["score"] is not None]
    avg_score = sum(scored) / len(scored) if scored else 0

    print(f"\n--- Summary ---")
    print(f"Judge parse success: {parsed_count}/{len(results)}")
    print(f"Average score (of parsed): {avg_score:.1f}/5")

    with open("results_stage2.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Full results saved to results_stage2.json")