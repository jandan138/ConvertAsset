"""Build the venue bibliography from primary-source metadata; record every correction."""
from pathlib import Path
import importlib.util,sys,re,html,json
s=importlib.util.spec_from_file_location('audit','/root/.codex/skills/citation-integrity-auditor/scripts/audit_citations.py');a=importlib.util.module_from_spec(s);sys.modules['audit']=a;s.loader.exec_module(a)
p=Path(__file__).resolve().parent.parent; root=p.parents[2]
all_entries={e.key:e for q in [root/'paper/shared/references.bib',p/'iclr_references.bib'] for e in a.parse_bibtex(q)[0]}
keys=set(k.strip() for f in p.rglob('*.tex') for group in re.findall(r'\\cite\w*\{([^}]+)\}',f.read_text()) for k in group.split(','));changes=[];entries={k:all_entries[k] for k in keys if k in all_entries}
def authors(k):return ' and '.join(html.unescape(x) for x in re.findall(r'<meta name="citation_author" content="([^"]*)"',(p/'citation_audit/sources'/f'{k}.html').read_text()))
for k in ['Bai2025Qwen','Zhu2025InternVL','Deitke2024Molmo']:
 e=entries[k];value=authors(k);changes.append({'key':k,'field':'author','before':e.fields['author'],'after':value,'reason':'Complete author list from primary landing-page metadata.'});e.fields['author']=value
k='Deitke2024Molmo';e=entries[k];changes.append({'key':k,'field':'publication','before':'arXiv, 2024','after':'CVPR, 2025, pp. 91–104','reason':'Use published proceedings version; retain citation key to avoid prose churn.'});e.fields.pop('journal');e.fields.update(year='2025',booktitle='Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition (CVPR)',pages='91--104',url='https://openaccess.thecvf.com/content/CVPR2025/html/Deitke_Molmo_and_PixMo_Open_Weights_and_Open_Data_for_State-of-the-Art_CVPR_2025_paper.html');entries[k]=a.BibEntry('inproceedings',k,e.fields)
k='Wei2026Ground';e=entries[k];before=e.fields['title'];e.fields['title']=before.replace('Vision-Language','Vision-and-Language');changes.append({'key':k,'field':'title','before':before,'after':e.fields['title'],'reason':'Original PDF title contains Vision-and-Language.'})
k='Bai2025Qwen3';entries[k]=a.BibEntry('article',k,dict(author=authors(k),title='{Qwen3-VL Technical Report}',journal='arXiv preprint arXiv:2511.21631',year='2025',url='https://arxiv.org/abs/2511.21631'))
k='Google2026Gemma4';entries[k]=a.BibEntry('misc',k,dict(author='{Google DeepMind}',title='{Gemma 4 model card}',year='2026',howpublished='Google AI for Developers',url='https://ai.google.dev/gemma/docs/core/model_card_4',note='Accessed September 15, 2026'))
for k in ['Bai2025Qwen3','Google2026Gemma4']:changes.append({'key':k,'field':'entry','before':None,'after':entries[k].fields,'reason':'Add attribution for evaluated checkpoint family; checkpoint configuration remains experiment provenance.'})
header='% ICLR-specific bibliography. Metadata corrections and primary evidence: citation_audit/corrections.json.\n% Internal key years are stable identifiers, not publication metadata.\n'
out=header+'\n\n'.join('@'+e.entry_type+'{'+k+',\n'+''.join('  '+f+' = {'+v+'},\n' for f,v in e.fields.items())+'}' for k,e in sorted(entries.items()))+'\n';(p/'references.bib').write_text(out)
(p/'citation_audit/corrections.json').write_text(json.dumps(changes,indent=2));print(len(entries),'entries; corrections',len(changes))
