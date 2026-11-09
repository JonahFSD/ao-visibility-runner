"""Compare matched successful observations only; descriptive, never causal."""
import argparse
import json
from pathlib import Path
from runner import records

def compare(before, after):
    before, after = Path(before), Path(after)
    a = json.loads((before/'manifest.json').read_text())['config']
    b = json.loads((after/'manifest.json').read_text())['config']
    for key in ('suite_hash', 'surface', 'engine', 'model', 'search_mode', 'locale', 'region', 'repetitions'):
        if a[key] != b[key]:
            raise ValueError('Incompatible comparison: ' + key)
    if a['demo'] or b['demo']:
        raise ValueError('Synthetic demos are not measurement baselines')
    ar = {r['key']:r for r in records(before/'evidence.jsonl') if r['status']=='ok'}
    br = {r['key']:r for r in records(after/'evidence.jsonl') if r['status']=='ok'}
    keys = sorted(ar.keys() & br.keys())
    result = {'matched_successful':len(keys), 'before_only_successful':len(ar.keys()-br.keys()),
              'after_only_successful':len(br.keys()-ar.keys()), 'interpretation':'descriptive, not causal', 'changes':[]}
    for key in keys:
        row = {'key':key}
        for metric in ('brand_mention_heuristic','owned_citation'):
            row[metric] = {'before':ar[key]['scores'][metric], 'after':br[key]['scores'][metric]}
        result['changes'].append(row)
    return result

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before'); parser.add_argument('after')
    args=parser.parse_args()
    try: print(json.dumps(compare(args.before,args.after),indent=2))
    except (ValueError, OSError) as exc: parser.exit(2,str(exc)+'\n')
