#!/usr/bin/env python3
"""NoLimit-style browser courier. No API, no browser/session interception."""
import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from runner import digest, load_suite, records, report, score, timestamp

ROOT = Path(__file__).resolve().parent


def open_session(directory):
    directory = Path(directory)
    manifest = json.loads((directory/'manifest.json').read_text())
    return directory, manifest, records(directory/'evidence.jsonl')


def pending(manifest, rows):
    done = {r['key'] for r in rows if r['status'] == 'ok'}
    # Round-robin questions before repetitions, matching NoLimit's balanced partial-run idea.
    return [(p, rep) for rep in range(1, manifest['config']['repetitions']+1)
            for p in manifest['prompts']['prompts'] if f"{p['id']}:{rep}" not in done]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    init = sub.add_parser('init')
    init.add_argument('directory'); init.add_argument('--model', required=True)
    init.add_argument('--effort', required=True); init.add_argument('--search-mode', required=True)
    init.add_argument('--settings-note', required=True, help='Observed personalization/settings; unknown must be stated')
    init.add_argument('--repetitions', type=int, default=1)
    for name in ('prompt','save','fail','status'):
        p = sub.add_parser(name); p.add_argument('directory')
        if name == 'prompt': p.add_argument('--copy', action='store_true')
        if name == 'save':
            p.add_argument('--key', required=True, help='Exact reservation key shown by prompt')
            p.add_argument('--citations', required=True, help='JSON file of observed source URLs; [] if observed none')
            p.add_argument('--evidence', required=True, help='Screenshot or transcript reference')
            p.add_argument('--notes', default=''); p.add_argument('--url', default='')
        if name == 'fail': p.add_argument('--reason', required=True)
    a = parser.parse_args()
    directory = Path(a.directory)
    if a.action == 'init':
        if a.repetitions < 1: raise ValueError('Repetitions must be positive')
        directory.mkdir(parents=True, exist_ok=True)
        suite = load_suite(ROOT/'prompts.json')
        config = {'suite_hash':digest(suite), 'version':suite['version'], 'surface':'consumer-ui-manual',
                  'engine':'ChatGPT browser', 'model':a.model, 'effort':a.effort, 'search_mode':a.search_mode,
                  'locale':'en-US', 'region':'unknown', 'repetitions':a.repetitions, 'demo':False,
                  'settings_note':a.settings_note}
        with (directory/'manifest.json').open('x') as f:
            json.dump({'config':config,'prompts':suite,**timestamp()},f,indent=2)
        print('Session initialized. No question sent.'); return
    directory, manifest, rows = open_session(directory)
    jobs = pending(manifest, rows)
    reservation = directory/'pending.json'
    if a.action == 'status':
        print(json.dumps({'saved':len(rows), 'remaining':len(jobs), 'next':jobs[0][0]['id'] if jobs else None})); return
    if not jobs: print('Complete. No prompts remain.'); return
    prompt, rep = jobs[0]
    key = f"{prompt['id']}:{rep}"
    if a.action == 'prompt':
        ticket = {'key':key,'prompt':prompt['text'],'suite_hash':manifest['config']['suite_hash']}
        if reservation.exists() and json.loads(reservation.read_text()) != ticket:
            raise ValueError('A different prompt is reserved; resolve it before continuing')
        reservation.write_text(json.dumps(ticket,indent=2))
        print(json.dumps(ticket,indent=2))
        if a.copy:
            if not shutil.which('pbcopy'): raise ValueError('pbcopy unavailable; use printed text')
            subprocess.run(['pbcopy'],input=prompt['text'],text=True,check=True)
        return
    if not reservation.exists(): raise ValueError('Run prompt first to reserve this question')
    if a.action == 'fail':
        with (directory/'failures.jsonl').open('a') as f:
            f.write(json.dumps({'key':key,'reason':a.reason,**timestamp()})+'\n')
        print('Failure preserved; question remains pending. Stop on account usage limits.'); return
    ticket = json.loads(reservation.read_text())
    if a.key != key or ticket['key'] != key: raise ValueError('Stale or incorrect answer key')
    answer = sys.stdin.read().strip()
    if len(answer)<20 or answer==prompt['text'].strip(): raise ValueError('Empty/short answer or prompt echo refused')
    citations = json.loads(Path(a.citations).read_text())
    if not isinstance(citations,list) or not all(isinstance(x,str) for x in citations): raise ValueError('Expected citation URL array')
    row = {'key':key,'prompt_id':prompt['id'],'prompt':prompt['text'],'repetition':rep,
           'suite_hash':manifest['config']['suite_hash'],'surface':'consumer-ui-manual', 'status':'ok',
           'answer':answer,'citations':citations,'scores':score(answer,citations),**timestamp(),
           'provider_metadata':{'evidence_reference':a.evidence,'chat_url':a.url,'notes':a.notes,
                                'model':manifest['config']['model'],'effort':manifest['config']['effort']}}
    with (directory/'evidence.jsonl').open('a') as f: f.write(json.dumps(row)+'\n')
    reservation.unlink()
    report(directory)
    print(f'Saved {key}; {len(jobs)-1} remaining')

if __name__=='__main__':
    try: main()
    except (ValueError,OSError,KeyError) as exc: sys.exit(str(exc))
