import hashlib, json, pathlib
root = pathlib.Path('/tmp/BugsInPy/projects')
rows = []
for f in root.glob('*/bugs/*/bug.info'):
    d = {}
    for line in f.read_text(errors='ignore').splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            d[k.strip()] = v.strip().strip('"')
    buggy = d.get('buggy_commit_id', '')
    if not buggy:
        continue
    project = f.parts[-4]
    bug = f.parts[-2]
    key = f'V52|{project}|{bug}|{buggy}'
    rows.append({
        'rank': hashlib.sha256(key.encode()).hexdigest(),
        'project': project,
        'bug': bug,
        'python_version': d.get('python_version', ''),
        'buggy_commit_id': buggy,
        'test_file': d.get('test_file', ''),
    })
rows.sort(key=lambda x: x['rank'])
out = pathlib.Path('artifacts/v52')
out.mkdir(parents=True, exist_ok=True)
(out / 'stream.json').write_text(json.dumps(rows, indent=2))
print(json.dumps(rows[:80], indent=2))
