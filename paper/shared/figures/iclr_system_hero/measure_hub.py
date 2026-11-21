"""Measure the quiet neutral face used by the editable glass-hub labels."""
from pathlib import Path
import json
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
HERE=Path(__file__).resolve().parent

def main():
    path=HERE/'assets/hub_glass_contained.png'
    im=Image.open(path).convert('RGBA');a=np.array(im);h,w=a.shape[:2]
    neutral=(a[:,:,:3].min(axis=2)>200)&(a[:,:,:3].max(axis=2).astype(int)-a[:,:,:3].min(axis=2).astype(int)<35)&(a[:,:,3]>100)
    window=[int(w*.15),int(h*.20),int(w*.85),int(h*.70)]
    allowed=np.zeros((h,w),bool);allowed[window[1]:window[3],window[0]:window[2]]=True
    labels,_=label(neutral & allowed,structure=np.ones((3,3),dtype=int));seed=(w//2,int(h*.42));cid=labels[seed[1],seed[0]]
    if cid==0:raise ValueError('Quiet-face seed is not a neutral pixel')
    filled=labels==cid;yy,xx=np.where(filled);bb=[int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)]
    info={'image':'assets/hub_glass_contained.png','seed':seed,'search_window_xyxy':window,'threshold':'RGB minimum >200, channel span <35, alpha >100','bbox_xyxy':bb,'pixels':int(filled.sum()),'purpose':'Measured face for editable text; no pixels repainted'}
    from build_hero import points
    layout=json.loads((HERE/'hero_A_glass.layout.json').read_text())
    by={it['id']:it for it in layout['items']};hx,hy,hw,hh=by['hub-art']['box']
    quiet=[hx+bb[0]/w*hw,hy+bb[1]/h*hh,hx+bb[2]/w*hw,hy+bb[3]/h*hh]
    info['quiet_face_inches']=quiet;info['text_ink_boxes']={}
    for key in ('hub-label','hub-function'):
        it=by[key];tw,th=points(it['text'],it['size'],it['font'],it['bold']);tx,ty,tww,thh=it['box']
        ink=[tx+(tww-tw)/2,ty+(thh-th)/2,tx+(tww+tw)/2,ty+(thh+th)/2]
        if not (ink[0]>=quiet[0] and ink[1]>=quiet[1] and ink[2]<=quiet[2] and ink[3]<=quiet[3]):raise ValueError(f'{key} exceeds measured quiet face')
        info['text_ink_boxes'][key]=ink
    info['text_containment']='PASS'
    (HERE/'assets/hub_face_measurement.json').write_text(json.dumps(info,indent=2)+'\n')
    preview=im.convert('RGB');d=ImageDraw.Draw(preview);d.rectangle(bb,outline='red',width=3);d.ellipse((seed[0]-6,seed[1]-6,seed[0]+6,seed[1]+6),fill='red');preview.save(HERE/'assets/hub_face_measurement.png')
    print(json.dumps(info))
if __name__=='__main__':main()
