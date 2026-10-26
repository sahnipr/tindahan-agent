"""Run invented conversation fixtures; placeholders bind live quote IDs."""
import json
from pathlib import Path
from agent import Agent
from tools import Sandbox

for path in sorted(Path(__file__).parent.joinpath('conversations').glob('*.json')):
    agent = Agent(Sandbox())
    fixture = json.loads(path.read_text())
    qid = ''
    for turn in fixture['turns']:
        text = turn.get('text', '').replace('{quote_id}', qid)
        reply = agent.reply('sample-store', text, turn.get('photos'))
        assert turn['expect'] in reply, (path.name, reply)
        if 'sample-store' in agent.pending:
            qid = agent.pending['sample-store']['id']
    assert len(agent.tools.orders) == fixture['orders']
    print('PASS', path.name)
