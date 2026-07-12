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

## Stage 2 — LLM-as-judge
- 3/3 judge outputs parsed successfully (format-following worked)
- Average score: 4.0/5
- CRITICAL FINDING: instruction_001 exposed a real judge failure.
  - System under test answered "Yes, the Earth is flat." -- factually
    wrong, AND violated the "answer with just yes or no" instruction.
  - Judge scored it 4/5, reason: "The answer is correct and clearly
    explained" -- this is VERBATIM the example reason text from the
    few-shot judge prompt template, not a genuine assessment.
  - Root cause: the judge pattern-matched onto the shape of the few-shot
    example instead of reasoning about the actual answer content. Known
    failure mode of few-shot prompting on small/weak models.
  - Implication: a judge's score is NOT ground truth. Judges must be
    validated against cases with a known correct verdict before being
    trusted -- this project only caught the failure because a human
    (me) happened to know the Earth isn't flat and read the raw output.
  - This is exactly why production systems use a STRONGER model as
    judge than as system-under-test, and why judge outputs should be
    spot-checked by humans periodically, not blindly trusted.

## Stage 2 — Judge prompt fix (few-shot example removed)
- Root cause confirmed: original judge prompt included a few-shot
  example ("SCORE: 4 / REASON: The answer is correct and clearly
  explained"). Judge was echoing this example verbatim instead of
  reasoning about actual answer content.
- Fix: removed the few-shot example, added explicit instruction
  ("Do not assume the answer is correct"), forced reasoning about
  "THIS answer" specifically.
- Result on instruction_001 (previously mis-scored 4/5):
  - NEW score: 1/5
  - NEW reason: genuine, answer-specific reasoning (flagged both the
    instruction violation AND factual error correctly)
  - Minor residual issue: reasoning phrasing is slightly garbled
    ("responded with just yes or no" -- backwards phrasing), likely
    a language quality limitation of the 0.5B model rather than a
    judgment error. Verdict (score) is correct even if prose isn't
    perfectly clean.
- Lesson: few-shot examples in judge prompts are a double-edged sword
  -- they help formatting compliance but risk the model copying the
  example's CONTENT, not just its structure. Especially risky on
  small/weak models with less capacity to generalize the pattern
  correctly.

## Stage 2 — Summary of judge reliability findings
Over several prompt iterations, the 0.5B judge exhibited FOUR distinct
failure modes on the same 3-case dataset:
1. Copying few-shot example CONTENT verbatim instead of reasoning
2. Copying prompt PLACEHOLDER SYNTAX (<1-5>, <your reasoning...>) literally
3. Failing to stop generation, producing multiple SCORE/REASON blocks
4. Echoing the ANSWER text back as the "reason" instead of judging it

Score for instruction_001 (known-bad answer: "Yes, the Earth is flat")
did correctly converge to 1/5 after prompt fixes -- but with internally
contradictory reasoning text ("The Earth is a sphere, and the Earth is
flat"), showing the VERDICT can be right even when the underlying
reasoning is not coherent.

CONCLUSION: a 0.5B model is not a reliable judge, even with careful
prompt engineering. This mirrors real industry practice: production
eval pipelines use a stronger, separate model for the judge role
specifically because judging requires more reliable reasoning than
raw generation quality alone. Score outputs from a weak judge should
be treated as noisy signal, spot-checked by humans, never as ground
truth.