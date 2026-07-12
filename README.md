# LLM Eval Pipeline

A from-scratch evaluation harness for LLM outputs — golden dataset,
rule-based checks, LLM-as-judge scoring, aggregated reporting, and
regression tracking. Built to understand how evaluation pipelines
actually work, and—more importantly—to understand exactly where and how
they break.

## The actual finding

This project set out to build a standard evaluation pipeline. It ended
up becoming a documented case study in **why small language models make
unreliable judges**, discovered empirically rather than assumed.

Over the course of building and debugging, the same **Qwen2.5-0.5B**
model—used as an LLM-as-judge—exhibited five distinct, reproducible
failure modes:

1. **Few-shot content copying**
   - Repeated the example score and reasoning verbatim, regardless of
     what it was actually evaluating.

2. **Placeholder syntax copying**
   - Generated literal placeholders such as `<1-5>` and
     `<your reasoning here>` instead of filling them in.

3. **Failure to stop generating**
   - Produced multiple `SCORE:` / `REASON:` blocks instead of stopping
     after the first evaluation.

4. **Answer echoing**
   - Copied the candidate answer into its reasoning instead of actually
     evaluating it.

5. **Score insensitivity**
   - Assigned identical scores to two meaningfully different answers
     (one complete, one intentionally truncated), failing to detect a
     genuine quality regression.

Every failure was captured with evidence—not merely hypothesized.
Raw outputs were preserved in `results_*.json` and documented in
`NOTES.md` as each issue was discovered.

## Why this matters

Many AI products ship with little or no systematic evaluation.
Even teams that build LLM-as-judge pipelines often assume that if the
judge returns a well-formatted score, the score is trustworthy.

This project demonstrates why that assumption is dangerous.

A judge can:

- Parse correctly.
- Produce clean numeric scores.
- Follow the requested format.

...while still silently copying nearby text, exhibiting reasoning
failures, or failing to recognize meaningful differences in answer
quality.

Production systems typically use a stronger, separate model for judging
because evaluation is often a more demanding capability than generation
itself. This project reproduces that lesson from direct experimental
evidence rather than accepting it as conventional wisdom.

## Pipeline stages

| Stage | Description |
|-------|-------------|
| 0 | Golden dataset — 7 hand-written test cases combining deterministic and open-ended evaluations |
| 1 | Rule-based evaluation — exact match and substring checks |
| 2 | LLM-as-judge — open-ended scoring, iterated through five documented failure modes |
| 3 | Aggregated reporting — deterministic and judge-based metrics reported separately, with explicit confidence labeling |
| 4 | Regression comparison — compares labeled runs and validates identical vs genuinely changed outputs |

## Results

### Rule-based evaluation

- **4/4 deterministic checks passed**
- Consistent across every run
- Fully reproducible

### LLM-as-judge evaluation

- **Average score:** **1.7 / 5** after multiple prompt iterations

The numeric score itself is less important than the engineering lessons
revealed while attempting to make the judge reliable.

### Regression testing

The regression comparison behaved correctly:

- No false positives on identical runs.
- Correctly identified when outputs differed.

However, introducing a genuine regression (truncating an answer from
approximately 60 tokens to 15 tokens) exposed a deeper problem:

- The regression tool detected that the answer changed.
- The underlying judge **did not change its score**.

In other words, the measurement pipeline functioned correctly while the
metric itself proved unreliable.

## Project structure

```text
llm-eval-pipeline/
├── golden_dataset.json         # 7 evaluation cases
├── stage1_rule_based.py        # Deterministic evaluation
├── stage2_llm_judge.py         # LLM-as-judge experiments
├── stage3_report.py            # Aggregated reporting
├── stage4_diff.py              # Baseline vs current regression comparison
├── requirements.txt
├── NOTES.md                    # Full build log and documented failures
└── README.md
```

## Setup

Runs entirely on CPU using **Qwen2.5-0.5B**.

No GPU or paid API is required.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the baseline evaluation:

```bash
python stage1_rule_based.py baseline
python stage2_llm_judge.py baseline
python stage3_report.py
```

After modifying prompts, code, or the model:

```bash
python stage1_rule_based.py current
python stage2_llm_judge.py current
python stage4_diff.py baseline current
```

## Key learnings

- **KV-cache generation** (reused from the Tiny Inference Server project)
  behaves identically whether the model is generating answers or
  evaluating them.

- **Few-shot prompting is risky for small judge models.**
  While it improves formatting, it also encourages copying of example
  content instead of genuine evaluation.

- **Correct scores do not imply coherent reasoning.**
  One evaluation correctly assigned **1/5**, yet justified it with
  contradictory reasoning ("the Earth is a sphere" and "the Earth is
  flat").

- **Rule-based and judge-based metrics should remain separate.**
  Combining them into a single score would obscure the unreliability
  uncovered during this project.

- **Regression infrastructure and evaluation quality are independent.**
  A regression framework can function perfectly while revealing that the
  metric it relies on is fundamentally unreliable.

## What's not built

Known limitations and logical next steps:

- Compare against a stronger external judge (e.g. Gemini or Claude) to
  quantify the limitations of Qwen2.5-0.5B.

- Add statistical significance testing and repeated-run confidence
  intervals instead of relying on single-run comparisons.

- Expand the golden dataset beyond seven examples to improve coverage
  and expose additional edge cases.

## Status

✅ Complete.

The project implements a full evaluation pipeline with deterministic
checks, LLM-as-judge scoring, reporting, and regression testing.

Its primary contribution is documenting—through reproducible evidence—the
failure modes encountered when using a small language model as an
automatic evaluator.

The complete development history, including every bug, experiment, and
judge failure, is documented in **`NOTES.md`**.