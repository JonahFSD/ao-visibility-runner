"""Import preserved, human-collected UI observations; never labels API as UI."""
import json
import os
import sys
from pathlib import Path
request = json.load(sys.stdin)
path = Path(os.environ['OBSERVATIONS_DIR']) / (request['prompt_id'] + '-' + str(request['repetition']) + '.json')
data = json.loads(path.read_text())
for field in ('collected_at', 'product', 'evidence_reference'):
    if not data.get('metadata', {}).get(field):
        raise ValueError('Manual observation requires provenance: ' + field)
if data.get('prompt') != request['prompt']:
    raise ValueError('Collected prompt differs from frozen question')
print(json.dumps(data))
