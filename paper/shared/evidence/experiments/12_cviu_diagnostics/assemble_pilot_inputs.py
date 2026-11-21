"""Join actual capture progress with hash-bound visual reviews, retaining provenance."""
import argparse,json,re,subprocess,sys
from pathlib import Path
from freeze_inputs import sha

def main():
 p=argparse.ArgumentParser();p.add_argument('--progress',type=Path,nargs='+',required=True);p.add_argument('--qa',type=Path,nargs='+',required=True);p.add_argument('--out',type=Path);a=p.parse_args()
 captures={}
 for f in a.progress:
  if not f.exists():continue
  for r in json.loads(f.read_text())['records']:
   if r['capture_status']=='captured_unreviewed':captures[str(Path(r['output']))]=r
 accepted={};reviews={}
 for f in a.qa:
  if not f.exists():continue
  for q in json.loads(f.read_text())['reviews']:
   if q['verdict']!='PASS':continue
   r=captures.get(str(Path(q['output'])))
   if not r:raise ValueError('PASS review has no capture record')
   if (q['pair_id'],q['condition'])!=(r['pair_id'],r['condition']):raise ValueError('Review/capture identity mismatch')
   directory=Path(r['output'])
   if sha(directory/'rgb.png')!=q['image_sha256'] or sha(directory/'target_mask.npy')!=q['mask_sha256']:raise ValueError('Reviewed artifact changed')
   key=(r['pair_id'],r['condition']);accepted[key]=r;reviews[key]=q
 pairs={k[0] for k in accepted};complete=[p for p in pairs if (p,'original') in accepted and (p,'converted') in accepted]
 for pair in complete:
  signatures=[]
  for c in ['original','converted']:
   text=Path(accepted[pair,c]['stage']).read_text()
   match=re.search(r'def Camera "DiagnosticCamera"\s*\{(.*?)\n\}',text,re.S)
   if not match:raise ValueError('Camera wrapper unavailable')
   signatures.append(' '.join(match.group(1).split()))
  if signatures[0]!=signatures[1]:raise ValueError('Paired camera mismatch: '+pair)
 print(json.dumps({'accepted_images':len(accepted),'complete_pairs':len(complete),'pair_ids':sorted(complete)}))
 if a.out is None:return
 if len(complete)<12 or len(accepted)!=2*len(complete):raise ValueError('Full paired coverage not ready; no dataset frozen')
 a.out.mkdir(parents=True,exist_ok=False)
 progress=a.out/'selected_progress.json';qa=a.out/'selected_qa.json'
 progress.write_text(json.dumps({'records':[accepted[k] for k in sorted(accepted)],'source_progress':[{'path':str(f),'sha256':sha(f)} for f in a.progress if f.exists()],'source_qa':[{'path':str(f),'sha256':sha(f)} for f in a.qa if f.exists()],'excluded_reviews':[q for f in a.qa if f.exists() for q in json.loads(f.read_text())['reviews'] if q['verdict']!='PASS']},indent=2)+'\n')
 qa.write_text(json.dumps({'reviews':[reviews[k] for k in sorted(reviews)]},indent=2)+'\n')
 subprocess.run([sys.executable,str(Path(__file__).with_name('freeze_inputs.py')),'--progress',str(progress),'--qa',str(qa),'--out',str(a.out/'manifest.json')],check=True)
if __name__=='__main__':main()
