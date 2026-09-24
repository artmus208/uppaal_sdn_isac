"""Native Windows smoke; output directory must be new. No baseline claim."""
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT/'src'))
sys.dont_write_bytecode = True
from uppaal_mcp import verification_manager as m

if __name__ == '__main__':
    out = Path(sys.argv[1]).resolve(); out.mkdir(parents=True, exist_ok=False)
    model = out/'input.xml'; queries = out/'input.q'
    model.write_text('''<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE nta PUBLIC '-//Uppaal Team//DTD Flat System 1.1//EN' 'http://www.it.uu.se/research/group/darts/uppaal/flat-1_2.dtd'>
<nta><declaration>clock x;</declaration><template><name>Clock</name>
<location id="s"><name>Ready</name><label kind="invariant">x &lt;= 1</label></location><init ref="s"/>
<transition><source ref="s"/><target ref="s"/><label kind="guard">x == 1</label><label kind="assignment">x = 0</label></transition>
</template><system>C = Clock(); system C;</system></nta>
''', encoding='utf-8')
    queries.write_text('A[] x <= 1\nA[] x < 1\n', encoding='utf-8')
    queue = out/'queue'
    m.initialize(queue, model, queries, sys.argv[2], timeout=30, memory_mib=256)
    code = m.start(queue, interval=.05)
    results = [m.read(p) for p in sorted(queue.glob('attempts/*/result.json'))]
    assert code == 0 and [r['verdict'] for r in results] == ['satisfied','violated']
    before = {str(p.relative_to(queue)):m.digest(p) for p in queue.glob('attempts/**/*') if p.is_file()}
    assert m.start(queue) == 0
    assert before == {str(p.relative_to(queue)):m.digest(p) for p in queue.glob('attempts/**/*') if p.is_file()}
    m.save(out/'smoke.json', {'kind':'software integration smoke, not frozen-baseline evidence',
           'manager_source_commit':sys.argv[3],
           'manager_hash':m.digest(m.__file__), 'smoke_script_hash':m.digest(__file__),
           'exit_code':code,'continuation_skipped_completed':True,
           'results':[{'run_id':r['run_id'],'status':r['status'],'verdict':r['verdict'],
           'model_hash':r['model_hash'],'query_hash':r['query_hash'],'tool_version':r['tool_version'],
           'elapsed_seconds':r['elapsed_seconds'],'peak_rss_bytes':r['peak_rss_bytes']} for r in results]})
    print('Native UPPAAL smoke and continuation checks OK')
