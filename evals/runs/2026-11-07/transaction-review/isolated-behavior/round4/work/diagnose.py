"""仅诊断：实际调用未修改的合成 fixture CLI，保留全部输出。"""
import json
import os
from pathlib import Path
import subprocess
import sys

root = Path('/workspace/shared/skill_evals_v4/round4')
work = root / 'work'
fixture = root / 'fixture'
alternate = work / 'matched-topic.json'
alternate.write_text(json.dumps({'error_topic': 'task.error'}) + '\n')
results = {}
for config_name, config in [('original', fixture / 'config.json'), ('matched', alternate)]:
    for event in ['idle', 'success', 'error']:
        command = [sys.executable, '-B', str(fixture / 'monitor.py'), '--config', str(config), '--event', event]
        print('$', ' '.join(command), flush=True)
        process = subprocess.run(command, capture_output=True, text=True, env={**os.environ, 'PYTHONDONTWRITEBYTECODE': '1'})
        print('exit_code:', process.returncode)
        print(process.stdout, end='')
        print('stderr:', repr(process.stderr))
        assert process.returncode == 0
        result = json.loads(process.stdout)
        results[config_name, event] = result
        (work / f'{config_name}-{event}.json').write_text(process.stdout)

original = results['original', 'error']
matched = results['matched', 'error']
assert original['source_log'] == [{'source': 'TaskRunner', 'event': 'task.error', 'request_id': 'fixture-001'}]
assert original['monitor']['status'] == 'RUNNING' and original['monitor']['error_count'] == 0
assert matched['source_log'][0] == original['source_log'][0]
assert matched['source_log'][1] == {'source': 'ErrorProbe', 'event': 'observed_error'}
assert matched['monitor']['status'] == 'FAILED' and matched['monitor']['error_count'] == 1
for event, expected in [('idle', 'RUNNING'), ('success', 'SUCCEEDED')]:
    assert results['original', event] == results['matched', event]
    assert results['original', event]['monitor']['status'] == expected
    assert results['original', event]['monitor']['error_count'] == 0
assert all(not r['ui']['button_enabled'] for r in results.values())
print('PASS: 6 actual CLI runs; error source retained, matching-only config restores probe/state; idle/success unchanged; UI disabled in every case.')
