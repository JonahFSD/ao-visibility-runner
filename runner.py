#!/usr/bin/env python3
"""Dependency-free evidence-first visibility harness. No network calls by default."""
import argparse
import concurrent.futures
import datetime as dt
import hashlib
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def load_suite(path):
    suite = json.loads(Path(path).read_text())
    prompts = suite['prompts']
    if len({p['id'] for p in prompts}) != len(prompts):
        raise ValueError('Duplicate prompt IDs')
    if not prompts or any(not p['text'].strip() for p in prompts):
        raise ValueError('Empty prompt suite/text')
    return suite


def score(answer, citations):
    # Exact entity signals only. Not a semantic recommendation/accuracy judgment.
    mention = bool(re.search(r"\bathlete(?:s[’']?|[’']s)\s+ocean\b|\bathletesocean\.com\b", answer, re.I))
    owned = []
    third = []
    for url in citations:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https') or not parsed.hostname:
            raise ValueError('Citation must be an absolute HTTP(S) URL')
        host = parsed.hostname.lower()
        (owned if host == 'athletesocean.com' or host.endswith('.athletesocean.com') else third).append(url)
    return {'brand_mention_heuristic': mention, 'owned_citation': bool(owned),
            'owned_urls': owned, 'third_party_urls': third,
            'recommendation': 'unreviewed', 'accuracy': 'unreviewed', 'human_review': 'pending'}


def validate_output(output):
    if not isinstance(output.get('answer'), str) or not output['answer'].strip():
        raise ValueError('Adapter requires nonempty answer string')
    if not isinstance(output.get('citations'), list) or not all(isinstance(x, str) for x in output['citations']):
        raise ValueError('Adapter requires citations array of observed URLs; [] if none')
    score(output['answer'], output['citations'])
    return output


def timestamp():
    now = dt.datetime.now(dt.timezone.utc)
    return {'timestamp_utc': now.isoformat(), 'timestamp_chicago': now.astimezone(ZoneInfo('America/Chicago')).isoformat()}


def records(path):
    if not Path(path).exists():
        return []
    return [json.loads(line) for line in Path(path).read_text().splitlines() if line.strip()]


def run(args):
    suite = load_suite(args.prompts)
    if args.repetitions < 1 or not 1 <= args.concurrency <= 20:
        raise ValueError('Repetitions >= 1 and concurrency 1..20 required')
    if not args.demo and (not args.command or not args.allow_live):
        raise ValueError('Live run requires --command and explicit --allow-live; adapters may incur costs')
    config = {'suite_hash': digest(suite), 'version': suite['version'], 'engine': args.engine,
              'model': args.model, 'surface': 'synthetic-demo' if args.demo else args.surface,
              'search_mode': args.search_mode, 'locale': args.locale, 'region': args.region,
              'repetitions': args.repetitions, 'command': args.command, 'demo': args.demo}
    folder = Path(args.out)
    folder.mkdir(parents=True, exist_ok=True)
    manifest_path = folder / 'manifest.json'
    if manifest_path.exists() and json.loads(manifest_path.read_text())['config'] != config:
        raise ValueError('Run configuration changed. Use a NEW output directory')
    if not manifest_path.exists():
        manifest_path.write_text(json.dumps({'config': config, 'prompts': suite, **timestamp()}, indent=2))
    evidence = folder / 'evidence.jsonl'
    prior = records(evidence)
    done = {r['key'] for r in prior}  # errors retained, never silently retried/overwritten
    jobs = [(p, rep) for p in suite['prompts'] for rep in range(1, args.repetitions + 1)
            if f"{p['id']}:{rep}" not in done]

    def work(job):
        prompt, rep = job
        row = {'key': f"{prompt['id']}:{rep}", 'prompt_id': prompt['id'], 'prompt': prompt['text'],
               'repetition': rep, 'suite_hash': config['suite_hash'], 'surface': config['surface'], **timestamp()}
        try:
            if args.demo:
                output = {'answer': 'SYNTHETIC DEMO: no model was queried. No visibility findings.', 'citations': []}
            else:
                # No shell interpolation; every invocation is independent. Adapter owns fresh session semantics.
                result = subprocess.run(shlex.split(args.command), input=json.dumps({'prompt': prompt['text'],
                    'prompt_id': prompt['id'], 'repetition': rep, 'settings': config}),
                    text=True, capture_output=True, timeout=args.timeout, check=False)
                if result.returncode:
                    raise RuntimeError(f'Adapter exit {result.returncode}; stderr not persisted to prevent secret leakage')
                output = validate_output(json.loads(result.stdout))
            row.update(status='demo' if args.demo else 'ok', answer=output['answer'], citations=output['citations'],
                       provider_metadata=output.get('metadata', {}), scores=None if args.demo else score(output['answer'], output['citations']))
        except (Exception,) as exc:
            row.update(status='error', error_type=type(exc).__name__, scores=None)
        row['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
        return row

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.concurrency) as pool:
        for row in pool.map(work, jobs):
            with evidence.open('a') as file:
                file.write(json.dumps(row) + '\n')
            print(json.dumps({'key': row['key'], 'state': row['status']}), flush=True)
    report(folder)


def report(folder):
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_text())
    rows = records(folder / 'evidence.jsonl')
    good = [r for r in rows if r['status'] == 'ok']
    n = len(good)
    expected = len(manifest['prompts']['prompts']) * manifest['config']['repetitions']
    metrics = {'expected': expected, 'successful': n, 'errors': sum(r['status'] == 'error' for r in rows),
               'demo': sum(r['status'] == 'demo' for r in rows), 'not_run': expected-len(rows),
               'mentions': sum(r['scores']['brand_mention_heuristic'] for r in good),
               'owned_citations': sum(r['scores']['owned_citation'] for r in good)}
    (folder / 'summary.json').write_text(json.dumps(metrics, indent=2))
    lines = ['# AI visibility evidence report', '', f"Surface: {manifest['config']['surface']}",
             f"Frozen suite: {manifest['config']['version']} / {manifest['config']['suite_hash']}",
             '', f"Successful observations: {n}/{expected}; errors: {metrics['errors']}; synthetic demo: {metrics['demo']}; not run: {metrics['not_run']}",
             f"Exact brand mention signals: {metrics['mentions']}/{n or 'N/A'}", f"Owned-domain citation signals: {metrics['owned_citations']}/{n or 'N/A'}", '',
             'Heuristics require human review. Citation presence does not establish recommendation or accuracy.',
             'GA4 / Search Console: not connected. No conversions or traffic inferred.',
             'API observations are not consumer ChatGPT/other UI observations. Before/after is descriptive, not causal.', '', '| Question | Repetition | Status | Mention | Owned citation |', '|---|---:|---|---|---|']
    for r in rows:
        s = r['scores'] or {}
        lines.append(f"| {r['prompt_id']} | {r['repetition']} | {r['status']} | {s.get('brand_mention_heuristic', 'unknown')} | {s.get('owned_citation', 'unknown')} |")
    (folder / 'report.md').write_text('\n'.join(lines) + '\n')
    return metrics


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('run')
    p.add_argument('--prompts', default=str(Path(__file__).with_name('prompts.json')))
    p.add_argument('--out', required=True)
    p.add_argument('--demo', action='store_true')
    p.add_argument('--allow-live', action='store_true')
    p.add_argument('--command', help='Adapter executable; JSON stdin/stdout. Never put secrets in this string.')
    p.add_argument('--engine', default='unconfigured')
    p.add_argument('--model', default='unknown')
    p.add_argument('--surface', choices=['api', 'consumer-ui-manual'], default='api')
    p.add_argument('--search-mode', default='unknown')
    p.add_argument('--locale', default='en-US')
    p.add_argument('--region', default='US')
    p.add_argument('--repetitions', type=int, default=1)
    p.add_argument('--concurrency', type=int, default=4)
    p.add_argument('--timeout', type=int, default=120)
    p = sub.add_parser('report')
    p.add_argument('directory')
    args = parser.parse_args()
    try:
        run(args) if args.action == 'run' else report(args.directory)
    except (ValueError, OSError, KeyError) as exc:
        parser.exit(2, f'{exc}\n')


if __name__ == '__main__':
    main()
