"""Validate all final source/context bindings and publish the complete TeX inventory."""
from pathlib import Path
import hashlib
import json
import re
p = Path(__file__).resolve().parent
root = p.parents[3]
x = json.loads((p/'audit.json').read_text())
ledger = json.loads((p/'human-support.json').read_text())
advisory = json.loads((p/'advisory-support.json').read_text())
sha = lambda q: hashlib.sha256(q.read_bytes()).hexdigest()
sources = x['inputs']['tex_sources']
tables = []
for record in sources:
    q = root/record['path']
    assert sha(q) == record['sha256'], q
    if q.parent.name == 'tables' or q.stem.endswith('_table'):
        assert not re.search(r'\\cite\w*', q.read_text()), q
        tables.append(record)
expected = {(o['citation_key'],o['context_sha256']) for o in x['occurrences']}
assert expected == {(o['citation_key'],o['context_sha256']) for o in ledger['entries']}
assert expected == {(o['citation_key'],o['context_sha256']) for o in advisory['entries']}
assert advisory['tex_source_set_sha256'] == x['inputs']['manuscript_source_set_sha256']
for field in ['bib','support_ledger','input_resolution_adapter','metadata_cache','metadata_normalization']:
    record = x['inputs'][field]
    assert sha(root/record['path']) == record['sha256'], field
for e in ledger['entries']:
    assert not e['checked_by'] and all(e[f] == 'NOT_CHECKED' for f in ['identity_status','support_status','retraction_status'])
source_hashes = json.loads((p/'source-hashes.json').read_text())['files']
for record in source_hashes:
    assert sha(p/record['path']) == record['sha256'], record['path']
normal = json.loads((p/'metadata-normalization.json').read_text())
assert sha(p/'metadata-cache.json') == normal['raw_cache_sha256']
assert sha(p/'normalize_metadata.py') == normal['script_sha256']
(p/'traversal-inventory.json').write_text(json.dumps({'rule':'Active main recursively resolved using venue-working-directory first, child-relative fallback; missing inputs fail. Historical snapshots excluded.','main_tex':x['inputs']['main_tex'],'sources':sources,'total_sources':len(sources),'citation_keys':x['cited_keys'],'key_context_pairs':len(expected)},indent=2))
(p/'supplemental-tex-inventory.json').write_text(json.dumps({'reason':'All listed tables are included in the authoritative audit via input-resolution adapter; each independently checked citation-free.','sources':tables},indent=2))
result = {'status':'PASS_BINDINGS','keys':len(x['cited_keys']),'contexts':len(expected),'tex_sources':len(sources),'citation_free_tables':len(tables),'source_hashes':len(source_hashes),'raw_resolver_verdict':json.loads((p/'raw-audit.json').read_text())['verdict'],'effective_verdict':x['verdict'],'machine_identity_pass':x['summary']['identity_pass'],'human_attestations':0,'manuscript_sha256':x['inputs']['manuscript_source_set_sha256']}
(p/'validation.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
