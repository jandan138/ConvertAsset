"""Cache official MDL dependency trees without changing material source bytes."""
import argparse,hashlib,json,re,urllib.parse,urllib.request
from pathlib import Path
HOSTS={'omniverse-content-production.s3-us-west-2.amazonaws.com','omniverse-content-production.s3.us-west-2.amazonaws.com'}
STDLIB={'anno','base','df','math','state','tex','limits','debug','scene','builtins'}
def normalize(uri):
 if not uri.startswith(('http:','https:')):return None
 return 'https://'+uri.split(':',1)[1].lstrip('/')
def relative_modules(text):
 return re.findall(r'\busing\s+([.\w:]+)\s+import\s',text)
def sibling_import_modules(text):
 # MDL 1.5 also emits unprefixed imports such as GlassUtils::get_color.
 return sorted(set(m.rsplit('::',1)[0] for m in re.findall(r'\bimport\s+([A-Za-z_]\w*(?:::[A-Za-z_*]\w*)+)\s*;',text)))
def module_url(url,module):
 return urllib.parse.urljoin(url,'/'.join(module.split('::'))+'.mdl')
def main():
 p=argparse.ArgumentParser();p.add_argument('--seeds',type=Path,required=True);p.add_argument('--cache',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 seeds=json.loads(a.seeds.read_text())['records'];pending=[r['url'] for r in seeds];seen=set();files=[];unresolved=[];runtime={}
 sdk=Path('/cpfs/user/zhuzihou/conda-managed/envs/embodied-eval-os-isaacsim41-py310/lib/python3.10/site-packages/omni/mdl/core');roots=[sdk/'Base',sdk/'mdl']
 while pending:
  url=normalize(pending.pop(0))
  if url in seen:continue
  seen.add(url);parts=urllib.parse.urlparse(url)
  if parts.netloc not in HOSTS or not parts.path.startswith('/Materials/'):raise ValueError('Non-whitelisted resource '+url)
  dest=a.cache/parts.netloc/parts.path.lstrip('/')
  if not dest.resolve().is_relative_to(a.cache.resolve()):raise ValueError('Path escape')
  dest.parent.mkdir(parents=True,exist_ok=True)
  try:
   if not dest.exists():
    with urllib.request.urlopen(url,timeout=60) as response:data=response.read()
    with dest.open('xb') as f:f.write(data)
   blob=dest.read_bytes();files.append({'url':url,'path':str(dest.resolve()),'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()})
   if dest.suffix=='.mdl':
    text=blob.decode('utf-8')
    for module in sibling_import_modules(text):pending.append(module_url(url,module))
    for texture in re.findall(r'texture_2d\(\s*"([^\"]+)"',text):pending.append(urllib.parse.urljoin(url,texture))
    for module in relative_modules(text):
     if module.startswith('.'):pending.append(module_url(url,module))
    modules=relative_modules(text)+re.findall(r'\bimport\s+(::[\w:*]+)\s*;',text)
    for module in modules:
     if not module.startswith('::'):continue
     names=[x for x in module.split('::') if x and x!='*']
     if not names or names[0] in STDLIB:continue
     candidates=[root.joinpath(*names[:n]).with_suffix('.mdl') for n in range(len(names),0,-1) for root in roots]
     found=next((x for x in candidates if x.is_file()),None)
     if found:runtime[module]={'path':str(found),'sha256':hashlib.sha256(found.read_bytes()).hexdigest()}
     else:unresolved.append({'url':url,'module':module,'error':'runtime_module_not_found'})
  except Exception as e:unresolved.append({'url':url,'error':repr(e)})
  print('fetched',len(files),'pending',len(pending),'errors',len(unresolved),flush=True)
 result={'status':'complete' if not unresolved else 'incomplete','files':files,'runtime_modules':runtime,'unresolved':unresolved}
 with a.out.open('x') as f:json.dump(result,f,indent=2)
 return int(bool(unresolved))
if __name__=='__main__':raise SystemExit(main())
