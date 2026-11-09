# Athlete's Ocean visibility runner

A small, dependency-free Python 3.11+ harness for a frozen cohort of 20 unbranded wrestling/grappling buying-intent questions. Local-first evidence, not a claim of AI market share. No credentials, live calls, schedule or fabricated results are included.

## Run safely now

```sh
python -m unittest discover -s tests -v
python runner.py run --demo --out runs/demo
cat runs/demo/report.md
```

Demo executes all 20 jobs but labels every result **synthetic-demo**, excludes them from visibility denominators, and makes no network calls. Console JSON lines expose completed job states, not invented model reasoning. This is a CLI/data foundation, not yet a graphical mission-control dashboard.

## Live API run (optional, explicit opt-in)

Choose and authorize an API model and spend limit first. Configure a provider-side budget/rate limit. Set `OPENAI_API_KEY` through your approved secret store or shell (never commit it) and `OPENAI_MODEL` to a supported Responses API model. This repo does not create credentials. Do not paste secrets into the command argument or logs.

```sh
python runner.py run --out runs/baseline-api \
  --engine openai --model "$OPENAI_MODEL" --surface api --search-mode web_search \
  --repetitions 3 --concurrency 2 --allow-live \
  --command 'python adapters/openai_responses.py'
```

60 requests at three repetitions. Search may add costs. `--allow-live` is a deliberate gate, not a dollar budget cap. There are no automatic retries, to prevent unexpected duplicate charges. API integration is provided but **not live-verified**; tests are offline. Provider availability/model support/rate limits must be checked before a real run. A searched OpenAI API answer is NOT a consumer ChatGPT observation. Independent requests contain only each frozen question; no Ocean background is injected. No persistent conversation is used.

## Manual consumer-UI observations

Use a fresh chat per question, fixed product/account/search settings/locale, and preserve the complete answer and displayed citations. Store `observations/q01-1.json` etc.:

```json
{"prompt":"COPY EXACT FROZEN QUESTION", "answer":"COMPLETE OBSERVED ANSWER", "citations":["https://actual-displayed-source.example/"], "metadata":{"collected_at":"2026-11-09T12:00:00-06:00","product":"Consumer product name","evidence_reference":"local screenshot/transcript path","search_mode":"observed mode"}}
```

Set `OBSERVATIONS_DIR` to that directory; then:

```sh
python runner.py run --out runs/baseline-ui --engine 'product-name' \
  --surface consumer-ui-manual --search-mode 'observed-mode' --allow-live \
  --command 'python adapters/manual.py'
```

This imports existing files, not browser automation. Missing observations become errors, not failed brand visibility. `collected_at` is the actual observation time; row timestamp is import time. Preserve evidence references locally; do not publish private session URLs.

## Evidence and repeatability

* `prompts.json` is a **draft, product-grounded** cohort, not established query demand or a claim that Noah supplied these exact words. Freeze/review before the baseline. Groups: discovery 1–5, techniques 6–10, membership 11–15, coaches/teams 16–20.
* `manifest.json` embeds exact prompts, SHA-256 suite fingerprint, model, surface, locale/region (declared, not geolocation enforcement), search settings and timestamps.
* `evidence.jsonl` contains full answer, observed citation URLs, provider metadata, exact prompt, repetition, UTC and America/Chicago timestamps, errors and tentative scores.
* `summary.json` and `report.md` separate successful, missing, error, and synthetic observations. Display both numerators and denominators. GA4/GSC are unconnected, not zero.
* Restart with identical arguments to resume jobs not yet written. A configuration change requires a new folder. Completed errors remain preserved; retry intentionally in a new run. Never run two processes into one output folder. Interrupted in-flight API requests might have been billed even if no row was saved.
* No claim-level source support is inferred from a citation. Exact entity matches and owned-domain citations are separate. Ambiguous “Ocean” is not a mention. Recommendations, factual accuracy and competitor classification need human review. Review positives, errors, and a negative sample.
* For December, reuse the exact suite and settings, report changes per prompt and coverage. Model revisions, indexing and randomness confound causal claims. Do not compare aggregates across different cohorts, surfaces or missing-data patterns.

## Adapter contract

Every independent invocation receives JSON on stdin: `prompt`, `prompt_id`, `repetition`, `settings`. Return JSON on stdout with a nonempty `answer`, observed `citations` array, optional `metadata`. Use an executable command, no shell scripts interpolated by the runner. Citations must be HTTP(S) URLs; never mine incidental prose URLs and call them provider citations. Commands and provider metadata must not contain secrets. Error types only are persisted to avoid leaking stderr credentials.

## Scope / next handoff

No repo publication, scheduled paid run, analytics integration, or production deployment is implicit. Next: review/freeze cohort, choose provider and budget, collect real baseline, human-review evidence, then add a read-only dashboard over these artifacts. Keep client evidence private and out of git. Test CI below is offline only.

Matched before/after export: `python compare.py runs/baseline-api runs/december-api > comparison.json`. Requires identical suite, surface and declared settings; excludes errors and reports unmatched coverage. Synthetic runs cannot be compared as measurements.
