# Build Notes

## Stage 0 — Golden dataset
- 7 test cases: 4 rule-based (2 contains, 1 exact_match, 1 weak contains),
  3 judge-based (open-ended)
- format_001 flagged intentionally as a WEAK test (checks for a comma,
  not correctness of the colors themselves)

## Stage 1 — Rule-based checker
- 4/4 rule-based checks passed
- Debugging note: geo_001's terminal output looked truncated/incomplete
  ("...The capital of ") due to the print statement's 60-char preview,
  NOT an actual generation failure. Checked raw results_stage1.json and
  confirmed full output correctly said "...capital of Nigeria is Abuja."
- Lesson: always verify against raw stored results when a printed
  summary looks suspicious -- display truncation can look like a bug
  when the underlying data is fine.