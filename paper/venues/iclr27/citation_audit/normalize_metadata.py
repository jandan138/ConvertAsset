"""Replay one evidenced Crossref name repair through the unchanged identity rules.

Raw audit/cache/source bytes are retained. This does not waive DOI/title/year checks.
"""
from pathlib import Path
import copy
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('official', '/root/.codex/skills/citation-integrity-auditor/scripts/audit_citations.py')
official = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = official
SPEC.loader.exec_module(official)
DOI = '10.1109/tip.2003.819861'
PDF_SHA = 'd643c9f72b90627ed206df46be1e91827e1423281903bf4dc1378e27bc303e2d'

def normalize(entry, attempt, record):
    output = copy.deepcopy(attempt)
    author = record.get('author', [{}])[0]
    first = entry.fields.get('author', '').split(' and ')[0].strip()
    if (entry.fields.get('doi', '').lower() == DOI
            and record.get('DOI', '').lower() == DOI
            and author.get('family') == 'Zhou Wang' and not author.get('given')
            and first in ('Zhou Wang', 'Wang, Zhou')
            and output['match']['authors'][0] == 'Zhou Wang'):
        names = output['match']['authors'][:]
        names[0] = 'Wang'
        output['match'] = official._metadata_match(entry, output['match']['title'], names, output['match']['year'])
    return output

def main():
    source = json.loads((ROOT/'sources/Wang2004Image-doi.json').read_text())['message']
    if hashlib.sha256((ROOT/'sources/Wang2004Image.pdf').read_bytes()).hexdigest() != PDF_SHA:
        raise ValueError('Evidence PDF changed; inspect before renewing normalization')
    cache_path = ROOT/'metadata-cache.json'
    raw_bytes = cache_path.read_bytes()
    cache = json.loads(raw_bytes)
    entry = next(e for e in official.parse_bibtex(ROOT.parent/'references.bib')[0] if e.key == 'Wang2004Image')
    raw = cache['entries'][entry.key]
    attempts = {a['backend']:a for a in raw['attempts']}
    attempt = attempts['crossref-doi']
    fixed = normalize(entry, attempt, source)
    # Recompute identity using original official resolver/classification, replaying
    # captured responses only. No network requests or manually assigned PASS state.
    official._crossref_by_doi = lambda e,t: normalize(e, attempt, source)
    official._primary_url = lambda *args: copy.deepcopy(attempts.get('primary-url'))
    official._crossref_search = lambda *args: copy.deepcopy(attempts.get('crossref-search'))
    official._openalex_search = lambda *args: copy.deepcopy(attempts.get('openalex'))
    official._dblp_search = lambda *args: copy.deepcopy(attempts.get('dblp'))
    replay = official.resolve_identity(entry, [], 0, True, None)
    # Focused counterexamples: genuine author disagreement, mismatching DOI,
    # wrong DOI target/title and incompatible year cannot pass this repair.
    results = {}
    for name,field,value in [('wrong_author','author','John Smith'),('wrong_doi','doi','10.1109/WRONG'),('wrong_title','title','A Completely Different Paper'),('wrong_year','year','1990')]:
        fields = dict(entry.fields);fields[field] = value
        bad = official.BibEntry(entry.entry_type,entry.key,fields)
        before = copy.deepcopy(attempt)
        before['match'] = official._metadata_match(bad, attempt['match']['title'], attempt['match']['authors'], attempt['match']['year'])
        after = normalize(bad,before,source)
        assert not after['match']['pass'], name
        results[name] = 'PASS_REJECTED'
    assert fixed['match']['pass'] and replay['machine_status'] == 'VERIFIED_PRIMARY'
    log = {'citation_key':entry.key,'raw_state':raw['machine_status'],'normalized_state':replay['machine_status'],
        'raw_author':source['author'][0],'normalized_name_fields':{'given':'Zhou','family':'Wang'},
        'rule':'Only the independently verified complete name Zhou Wang incorrectly stored in Crossref family, with absent given and exact DOI; original title/year/author checks rerun.',
        'source_locator':'Original journal PDF p.1 (printed p.600): author line and DOI',
        'pdf_sha256':PDF_SHA,'source_url':'https://www.cns.nyu.edu/pub/lcv/wang03-reprint.pdf',
        'raw_cache_sha256':hashlib.sha256(raw_bytes).hexdigest(),'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'raw_match':attempt['match'],'normalized_match':fixed['match'],'regression_checks':results,'human_attestation':False}
    cache['entries'][entry.key] = replay
    (ROOT/'normalized-metadata-cache.json').write_text(json.dumps(cache,indent=2,sort_keys=True)+'\n')
    (ROOT/'metadata-normalization.json').write_text(json.dumps(log,indent=2)+'\n')
    assert cache_path.read_bytes() == raw_bytes
    print('PASS: evidenced SSIM name normalization; 4 negative identity regressions; raw cache unchanged')

if __name__ == '__main__':
    main()
