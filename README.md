# Athlete's Ocean: 20-question ChatGPT browser runner

Repurposes Jonah's **NoLimit browser courier** workflow, not an API. Twenty fixed wrestling/grappling questions go into fresh ChatGPT browser chats; observed answers and citations come back verbatim into a private, resumable evidence ledger.

Start with [BROWSER_RUNBOOK.md](BROWSER_RUNBOOK.md). The runner supplies `init`, `prompt`, `save`, `fail`, and `status`; your authorized browser agent drives the UI. It does not automate browsers through hidden endpoints or grab session credentials. No API adapter is included.

```sh
python3.12 -m unittest discover -s tests -v
python3.12 browser_runner.py --help
```

Record actual visible model, effort, search mode and personalization before initializing. Use one dedicated task tab, fresh temporary chat for every prompt, and stop at usage limits. The same account's personalization may still affect answers; unknown settings are a documented confound, not silently assumed clean.

## Outputs
`manifest.json`: frozen prompt cohort/hash and observed settings.
`evidence.jsonl`: raw answer, citations, prompt/key, observed model/effort, timestamps, evidence references and tentative mention/citation scores.
`failures.jsonl`: preserved failures without consuming a question.
`report.md` / `summary.json`: successful/missing counts; errors never treated as negative results.

Exact brand mentions and owned-domain citations are separate. Ambiguous “Ocean” is not a mention. Recommendations, factual accuracy and competitors require human review. No GA4, Search Console, traffic or conversion data is claimed.

`prompts.json` is a product-grounded **draft**, not a claim these were Noah's verbatim questions or validated demand. Freeze before baseline. All questions remain unbranded. `compare.py` compares matched successful observations with compatible settings; descriptive only, not causal proof.

The original generic offline demo/export utility `runner.py` remains for report functions and test fixtures, not as the ChatGPT collection entry point. Demo output is synthetic and excluded from real metrics. No real ChatGPT baseline has been collected in this repo yet. There is no graphical dashboard or scheduled monitor.

## Privacy
Runs and observations are gitignored. Keep transcripts/screenshots private. No secrets are required or stored. Browser control must use the current environment's supported browser tools. Preserve user tabs, settings and sessions; never switch accounts or bypass rate limits.
