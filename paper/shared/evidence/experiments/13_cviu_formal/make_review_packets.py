"""Derived original-only QA sheets. Never overwrite model RGB inputs."""
import argparse,hashlib,json
from collections import defaultdict
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFilter
p=argparse.ArgumentParser();p.add_argument('--captures',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--label-condition',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True);packets=[]
for progress in sorted(a.captures.glob('*/progress.json')):
 try:data=json.loads(progress.read_text())
 except (OSError,json.JSONDecodeError):continue
 groups=defaultdict(list)
 for r in data['records']:groups[r['target_prim']].append(r)
 for target,rows in groups.items():
  uid=hashlib.sha256(target.encode()).hexdigest()[:16];scene=rows[0]['scene_id'];directory=a.out/scene;directory.mkdir(exist_ok=True)
  sheet=Image.new('RGB',(1024,808),'white');draw=ImageDraw.Draw(sheet);frames=[]
  for i,r in enumerate(rows[:4]):
   folder=Path(r['output']);image=folder/'rgb.png';mask=folder/'target_mask.npy'
   if not image.exists() or not mask.exists():continue
   rgb=Image.open(image).convert('RGB');m=np.load(mask)
   eroded=np.asarray(Image.fromarray(m.astype('uint8')*255).filter(ImageFilter.MinFilter(3)))>0;edge=m&~eroded;arr=np.array(rgb);arr[edge]=[0,220,80]
   x=(i%2)*512;y=(i//2)*404;sheet.paste(Image.fromarray(arr).resize((512,384)),(x,y+20));draw.text((x+4,y+3),f"{r['pair_id'].rsplit(':',1)[1]}{(' '+r.get('condition','')) if a.label_condition else ''} | pixels {int(m.sum())} | {r['status']}",fill='black')
   frames.append({'pair_id':r['pair_id'],'output':str(folder),'image_sha256':r['image_sha256'],'mask_sha256':r['mask_sha256'],'status':r['status'],'mask_pixels':int(m.sum())})
  file=directory/(uid+'.png');sheet.save(file);packets.append({'scene_id':scene,'target_prim':target,'source_category':rows[0]['category'],'packet':str(file),'frames':frames,'review_status':'pending'})
(a.out/'packets.json').write_text(json.dumps({'packets':packets,'purpose':'Green contour marks USD instance for QA only; original model images unmodified'},indent=2)+'\n');print('review packets',len(packets))
