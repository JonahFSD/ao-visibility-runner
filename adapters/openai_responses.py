#!/usr/bin/env python3
"""Optional live adapter. Requires OPENAI_API_KEY, OPENAI_MODEL; no keys stored."""
import json
import os
import sys
import urllib.request

request = json.load(sys.stdin)
payload = {'model': os.environ['OPENAI_MODEL'], 'input': request['prompt'], 'store': False}
if request['settings']['search_mode'] == 'web_search':
    payload['tools'] = [{'type': 'web_search'}]
    payload['tool_choice'] = 'required'
response_request = urllib.request.Request('https://api.openai.com/v1/responses',
    data=json.dumps(payload).encode(), headers={'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'],
    'Content-Type': 'application/json'}, method='POST')
with urllib.request.urlopen(response_request, timeout=100) as response:
    raw = json.load(response)
if raw.get('status') != 'completed':
    raise RuntimeError('Provider response not completed')
text, citations = [], []
for item in raw.get('output', []):
    for part in item.get('content', []):
        if part.get('type') == 'output_text':
            text.append(part['text'])
            for annotation in part.get('annotations', []):
                if annotation.get('type') == 'url_citation':
                    citations.append(annotation['url'])
print(json.dumps({'answer': '\n'.join(text), 'citations': list(dict.fromkeys(citations)),
    'metadata': {'response_id': raw.get('id'), 'model': raw.get('model'), 'usage': raw.get('usage'),
                 'search_requested': request['settings']['search_mode'] == 'web_search',
                 'search_observed': any(x.get('type') == 'web_search_call' for x in raw.get('output', [])),
                 'raw_response': raw}}))
