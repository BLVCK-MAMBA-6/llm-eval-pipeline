import json


def load_results():
    with open("results_stage1.json") as f:
        rule_based = json.load(f)
    with open("results_stage2.json") as f:
        judge_based = json.load(f)
    return rule_based, judge_based


def generate_report(rule_based, judge_based):
    lines = []
    lines.append("=" * 60)
    lines.append("EVAL REPORT")
    lines.append("=" * 60)

    # --- Rule-based section: high confidence, deterministic ---
    total_rule = len(rule_based)
    passed_rule = sum(r["passed"] for r in rule_based)
    lines.append(f"\n[RULE-BASED CHECKS] -- deterministic, high confidence")
    lines.append(f"Passed: {passed_rule}/{total_rule}")
    for r in rule_based:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"  [{status}] {r['id']} ({r['type']})")

    # --- Judge-based section: explicitly flagged as lower confidence ---
    total_judge = len(judge_based)
    scored = [r["score"] for r in judge_based if r["score"] is not None]
    avg_judge = sum(scored) / len(scored) if scored else 0

    lines.append(f"\n[JUDGE-BASED SCORES] -- ⚠️  LOW CONFIDENCE")
    lines.append(f"⚠️  Judge model (Qwen 0.5B) has documented reliability issues:")
    lines.append(f"   answer-echoing, template-copying, inconsistent reasoning.")
    lines.append(f"   Treat these scores as ROUGH SIGNAL, not ground truth.")
    lines.append(f"Average score: {avg_judge:.1f}/5 (n={len(scored)})")
    for r in judge_based:
        flag = "" if r["parsed_ok"] else " ⚠️  PARSE FAILED"
        lines.append(f"  {r['id']}: {r['score']}/5{flag} -- {r['reason'][:60]}")

    # --- Overall summary, kept SEPARATE, not merged into one score ---
    lines.append(f"\n" + "=" * 60)
    lines.append(f"SUMMARY")
    lines.append(f"=" * 60)
    lines.append(f"Rule-based (trustworthy):  {passed_rule}/{total_rule} passed")
    lines.append(f"Judge-based (low confidence, needs human spot-check): {avg_judge:.1f}/5 avg")

    return "\n".join(lines)


if __name__ == "__main__":
    rule_based, judge_based = load_results()
    report = generate_report(rule_based, judge_based)
    print(report)

    with open("eval_report.txt", "w") as f:
        f.write(report)
    print("\n\nFull report saved to eval_report.txt")