import json
import sys


def load_run(stage, label):
    with open(f"results_stage{stage}_{label}.json") as f:
        return json.load(f)


def diff_rule_based(baseline, current):
    baseline_by_id = {r["id"]: r for r in baseline}
    current_by_id = {r["id"]: r for r in current}

    changes = []
    for id_, base_r in baseline_by_id.items():
        cur_r = current_by_id.get(id_)
        if cur_r is None:
            changes.append(f"  ⚠️  {id_}: missing from current run")
            continue
        if base_r["passed"] != cur_r["passed"]:
            direction = "REGRESSION (was passing, now failing)" if base_r["passed"] else "IMPROVEMENT (was failing, now passing)"
            changes.append(f"  {id_}: {direction}")
    return changes


def diff_judge_based(baseline, current, threshold=1):
    baseline_by_id = {r["id"]: r for r in baseline}
    current_by_id = {r["id"]: r for r in current}

    changes = []
    for id_, base_r in baseline_by_id.items():
        cur_r = current_by_id.get(id_)
        if cur_r is None or base_r["score"] is None or cur_r["score"] is None:
            continue
        diff = cur_r["score"] - base_r["score"]
        if abs(diff) >= threshold:
            direction = "IMPROVED" if diff > 0 else "REGRESSED"
            changes.append(f"  {id_}: {direction} ({base_r['score']} -> {cur_r['score']})")
    return changes


if __name__ == "__main__":
    baseline_label = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    current_label = sys.argv[2] if len(sys.argv) > 2 else "current"

    rule_baseline = load_run(1, baseline_label)
    rule_current = load_run(1, current_label)
    judge_baseline = load_run(2, baseline_label)
    judge_current = load_run(2, current_label)

    print(f"Comparing '{baseline_label}' -> '{current_label}'\n")

    print("[RULE-BASED CHANGES]")
    rule_changes = diff_rule_based(rule_baseline, rule_current)
    if rule_changes:
        for c in rule_changes:
            print(c)
    else:
        print("  No changes -- all rule-based results identical.")

    print("\n[JUDGE-BASED CHANGES] (score shift >= 1 point)")
    judge_changes = diff_judge_based(judge_baseline, judge_current)
    if judge_changes:
        for c in judge_changes:
            print(c)
    else:
        print("  No changes >= 1 point -- treat with caution given judge noise/unreliability.")