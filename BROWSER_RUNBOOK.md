# Browser courier runbook

Adapted from JonahFSD/NoLimit `analysis/llm_field/agent_sample.py`, `collect.py`, and `AGENT_RUNBOOK.md`, inspected at commit `108bb8bfaa52117ce0921d04d1930f07fd32b274`. Reuses its prompt/save/fail/status design, independent fresh-chat sampling, verbatim answers and resumable collection. No castle data copied.

The shell script manages evidence; an authorized browser agent or human drives ChatGPT's visible UI. It is NOT a headless scraping script. Use only the browser tool supported by the current environment. No API keys, hidden endpoints, session-token extraction, CDP, standalone Playwright, account switching or limit bypass.

1. Inspect the visible ChatGPT model, effort and search controls. Record exact labels, personalization/custom instructions state and settings you could not inspect. Do not change account settings without approval. Temporary Chat alone does not prove custom instructions are disabled. A baseline with unknown personalization must disclose that confound.
2. Initialize once with actual observed settings:
   `python3.12 browser_runner.py init runs/chatgpt-november --model 'EXACT VISIBLE LABEL' --effort 'EXACT VISIBLE LABEL OR NOT EXPOSED' --search-mode 'EXACT OBSERVED MODE' --settings-note 'Observed settings and unknowns'`
3. `python3.12 browser_runner.py prompt runs/chatgpt-november` prints the next prompt and reservation key. Optional `--copy` is for human clipboard use, not permission to bypass browser-tool clipboard rules.
4. Open a NEW temporary ChatGPT chat in a dedicated task tab. Verify settings for every question. Do not use an existing chat or project. Send exactly the printed question once, with no Ocean brief, no follow-up, and no regenerated answer. Stay within UI usage limits. Default one tab/one job at a time; browser-session safety beats impressive concurrency.
5. Wait for visible completion (stop control gone, answer complete/copy control present). Capture ONLY the final answer verbatim and preserve a screenshot/transcript. Record real displayed citations separately into a JSON URL array. Never transform incidental links into supposed citation evidence, invent citations, or expose chain-of-thought. Note search use only if observed. Do not use blind sleeps instead of UI state checks.
6. Save with the exact reservation key:
   `python3.12 browser_runner.py save runs/chatgpt-november --key q01:1 --citations citations.json --evidence 'screenshots/q01.png' < answer.txt`
   Optional `--url` and `--notes` preserve provenance. Temporary chats can have blank URLs. Keep evidence private. Capture time is recorded UTC and America/Chicago.
7. For an error use `python3.12 browser_runner.py fail runs/chatgpt-november --reason 'observed error'`. This does not consume a sample. Stop on usage limits and record reset time; do not switch accounts or evade limits. Never retry a possibly still-running submission.
8. If a question was submitted and its answer cannot be recovered, log the observed failure and then use `python3.12 browser_runner.py unknown runs/chatgpt-november --key q01:1` with its exact reservation key. This closes the job as unknown and allows collection to continue without resubmitting it.
9. `python3.12 browser_runner.py status runs/chatgpt-november` shows saved answers, closed unknowns and the next pending question. Keep one process per output folder. Review `report.md` and underlying evidence. Errors are unknown, not brand absence.

Target initially 20 actual browser answers. For a three-replicate study initialize with `--repetitions 3` (60 answers), balanced question-round-robin. Preserve exact cohort/settings for December and run `python3.12 compare.py BEFORE AFTER`. Human-review positive mentions, recommendation claims and answer accuracy.

## Test boundary
Offline tests validate reservation, echo rejection, saving and resume behavior. They do not establish that the browser is connected, that ChatGPT was queried, or that selectors work. There are deliberately no persistent selectors: the browser agent grounds every action in the visible UI. Report live collection separately.
