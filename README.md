# LLM Eval Pipeline

A from-scratch evaluation harness for LLM outputs — built to understand
how real eval pipelines work, not just call `model.generate()` and hope
for the best.

## Why this exists

Most AI products (including production ones) ship with zero systematic
evaluation — just vibes-based manual testing. This project builds a real
eval pipeline: a golden dataset, rule-based checks for objectively
verifiable answers, LLM-as-judge scoring for open-ended answers, and a
regression report that shows whether a prompt/model change made things
better or worse.

## Stages

- [ ] Stage 0 — Golden dataset: hand-written test cases with expected criteria
- [ ] Stage 1 — Rule-based checks (exact match, contains, regex) for verifiable answers
- [ ] Stage 2 — LLM-as-judge scoring for open-ended answers
- [ ] Stage 3 — Full pipeline: run all test cases, aggregate scores, generate a report
- [ ] Stage 4 — Regression tracking: compare two runs (e.g. before/after a prompt change)

## Setup

CPU-only. Reuses Qwen2.5-0.5B as the system under test.

```bash
pip install -r requirements.txt
```

## Status

🚧 In progress — Stage 0
