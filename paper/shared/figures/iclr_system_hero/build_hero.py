#!/usr/bin/env python3
"""Build two native PPTX/SVG hero figures from one layout and registered assets."""
from __future__ import annotations
import argparse
import base64
import hashlib
import html
import json
import math
import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml.xmlchemy import OxmlElement
from pptx.util import Inches, Pt

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'CLAUDE.md').exists())
W,H=12.0,6.0
O,C,INK,MUTED,LINE='0F4D92','E67E22','243247','63738A','BDCAD9'
TARGET='168A75'
FONTS={'sans':'Liberation Sans','serif':'Liberation Serif'}
FONTDIR=Path('/usr/share/fonts/truetype/liberation')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def rgb(value):return RGBColor.from_string(value)
def points(text,size,font='sans',bold=False):
    family='LiberationSans' if font=='sans' else 'LiberationSerif'
    f=ImageFont.truetype(str(FONTDIR/f'{family}-{"Bold" if bold else "Regular"}.ttf'),round(size*4))
    lines=text.split('\n')
    width=max(f.getlength(line) for line in lines)/288
    height=len(lines)*size*1.18/72
    return width,height


class Layout:
    def __init__(self):self.items=[];self.edges=[];self.ports=[];self.overlays=[]
    def add(self,kind,name,**kwargs):
        item={'kind':kind,'id':name,**kwargs};self.items.append(item);return item
    def text(self,name,text,x,y,w,h,size=15.5,color=INK,bold=False,align='left',font='sans',overlay=None):
        if overlay:self.overlays.append([name,overlay])
        return self.add('text',name,text=text,box=[x,y,w,h],size=size,color=color,bold=bold,align=align,font=font)
    def rect(self,name,box,fill='FFFFFF',stroke=None,lw=.7,radius=0):
        return self.add('rect',name,box=list(box),fill=fill,stroke=stroke,lw=lw,radius=radius)
    def image(self,name,path,box,border=None):
        path=HERE/path
        with Image.open(path) as im:iw,ih=im.size
        x,y,w,h=box;k=min(w/iw,h/ih);bw,bh=iw*k,ih*k
        return self.add('image',name,path=str(path.relative_to(HERE)),box=[x+(w-bw)/2,y+(h-bh)/2,bw,bh],stroke=border,lw=.8)
    def line(self,name,route,color=LINE,lw=1,head=False,dash=False,meaning=None,owners=None):
        item=self.add('line',name,points=[list(p) for p in route],color=color,lw=lw,head=head,dash=dash)
        if meaning:
            a,b=name+'.out',name+'.in'
            for pid,xy,owner in [(a,route[0],owners[0]),(b,route[-1],owners[1])]:
                self.ports.append({'id':pid,'owner':owner,'x':xy[0]*100,'y':xy[1]*100,'scope':'external'})
            self.edges.append({'id':name,'from':a,'to':b,'scope':'external','meaning':meaning,'arrowhead':'end' if head else 'none','route':'explicit','points':[{'x':x*100,'y':y*100} for x,y in route],'color':'#'+color,'width':lw,'dash':'dashed' if dash else 'solid'})
        return item
    def dot(self,name,x,y,r,color,shape='circle'):
        return self.add('dot',name,box=[x-r,y-r,r*2,r*2],color=color,shape=shape)


def prep_hub():
    source=HERE/'assets/hub_glass.png';out=HERE/'assets/hub_glass_contained.png'
    with Image.open(source) as im:
        a=np.asarray(im.getchannel('A'));mask=a>32
        rows=np.where(mask.sum(axis=1)>35)[0];cols=np.where(mask.sum(axis=0)>35)[0]
        pad=24;x0=max(0,int(cols[0])-pad);x1=min(im.width,int(cols[-1])+pad+1);y0=max(0,int(rows[0])-pad);y1=min(im.height,int(rows[-1])+pad+1)
        im.crop((x0,y0,x1,y1)).save(out)
    (HERE/'assets/hub_extraction.json').write_text(json.dumps({'source':'assets/hub_glass.png','source_sha256':sha(source),'crop_xyxy':[x0,y0,x1,y1],'purpose':'remove transparent padding only; preserve generated device pixels','output_sha256':sha(out)},indent=2)+'\n')
    return out.relative_to(HERE)


def point_panel(lay,name,record,box,color,marker):
    x,y,w,h=box
    lay.rect(name,box,'F9FBFD',LINE,.7)
    iw,ih=record['size'];x0,y0,x1,y1=record['bbox_xyxy_pixels']
    lay.rect(name+'.target',(x+x0/iw*w,y+y0/ih*h,(x1-x0)/iw*w,(y1-y0)/ih*h),None,TARGET,1)
    px,py=record['point_pixels'];lay.dot(name+'.prediction',x+px/iw*w,y+py/ih*h,.045,color,marker)


def build_layout(variant,manifest):
    l=Layout()
    # Same alignment and evidence for both variants; only the hub treatment changes.
    title='Same Scene, Different Decisions'
    l.text('headline',title,.15,.08,11.7,.44,28,O,True,'center','serif')
    l.text('materials-title','Material rewrites',.12,.62,2.35,.31,18,INK,True)
    l.text('original-label','Original',.12,.99,1.10,.28,15.5,O,True,'center')
    l.text('converted-label','Converted',1.36,.99,1.1,.28,15.5,C,True,'center')
    for i,name in enumerate(['wood','stone','ceramic','metal']):
        y=1.32+i*.94
        l.image(name+'.original',manifest['materials'][name+'_source']['file'],(.17,y,.86,.67))
        l.image(name+'.converted',manifest['materials'][name+'_simplified']['file'],(1.43,y,.86,.67))
        l.line(name+'.rewrite',[(1.07,y+.32),(1.37,y+.32)],O,.8,True)
        l.text(name+'.label',name.title(),.24,y+.67,2.02,.24,15.5,MUTED,False,'center')
        l.line(name+'.association',[(2.32,y+.32),(2.58,y+.32)],'8B9EB5',1.0,meaning=f'Illustrative {name} pair describes material rewrite behavior; not an input/output processing step.',owners=('materials','hub'))
    l.line('examples-bracket',[(2.58,1.64),(2.58,4.46)],'8B9EB5',1.0)
    l.line('examples-to-hub',[(2.58,2.96),(2.88,2.96)],'8B9EB5',1.0)
    # Small conceptual shader graphs, with native editable elements.
    for i,col in enumerate([O,C]):
        x=.19+i*1.26;y=5.19
        l.rect('shader-bg'+str(i),(x,y,.89,.41),'F4F7FA',LINE,.6,.06)
        nodes=[(x+.12,y+.10),(x+.12,y+.29),(x+.68,y+.20)]
        for j,(nx,ny) in enumerate(nodes):l.rect(f'shader-{i}-{j}',(nx-.055,ny-.035,.11,.07),col)
        for j in [0,1]:l.line(f'shader-edge-{i}-{j}',[nodes[j],nodes[2]],col,.7)['foreground']=True
    l.line('shader-rewrite',[(1.14,5.4),(1.39,5.4)],MUTED,.8,True)
    l.text('mdl','USD / MDL',.11,5.67,1.16,.25,15.5,O,False,'center')
    l.text('preview','Preview',1.40,5.67,1.08,.25,15.5,C,False,'center')
    # Hub appearance is replaceable; all labels remain native text.
    if variant=='glass':
        l.image('hub-art','assets/hub_glass_contained.png',(2.76,1.78,2.58,2.94))
        l.text('hub-label','ConvertAsset',2.87,2.82,2.35,.39,21,O,True,'center','serif','hub-art')
        l.text('hub-function','Material\nconversion',3.17,3.22,1.72,.55,15.5,INK,False,'center','sans','hub-art')
    else:
        l.rect('hub-card',(2.89,2.35,2.29,1.57),'F2F6FB',O,1,.10)
        l.rect('hub-accent',(2.89,2.35,2.29,.06),O)
        l.text('hub-label','ConvertAsset',2.94,2.79,2.18,.39,21,O,True,'center','serif')
        l.text('hub-function','Material conversion',2.94,3.29,2.18,.29,15.5,MUTED,False,'center')
    l.text('hub-operation','MDL →\nUsdPreviewSurface',2.74,4.83 if variant=='glass' else 4.20,2.60,.55,15.5,INK,False,'center')
    l.text('geometry','Geometry retained',2.82,5.51 if variant=='glass' else 4.91,2.43,.28,15.5,MUTED,False,'center')
    # Parallel evaluation branches; source-pair examples are not supplied to navigation.
    l.line('hub-grounding',[(5.18,2.91),(5.37,2.91),(5.37,.77),(5.61,.77)],C,1.1,True,meaning='The conversion protocol supports paired GRScenes grounding evaluation.',owners=('hub','grounding'))
    l.line('hub-navigation',[(5.18,3.18),(5.37,3.18),(5.37,3.74),(5.61,3.74)],C,1.1,True,meaning='The same intervention protocol is evaluated separately in KuJiaLe navigation.',owners=('hub','navigation'))
    l.text('grounding-title','Visual Grounding',5.66,.61,3.32,.31,18,O,True)
    l.text('query','“Locate the bottle”',9.03,.63,2.74,.29,15.5,INK,False,'right')
    obs=manifest['grounding']
    for i,(key,col,label) in enumerate([('two_view_category_original',O,'Original'),('two_view_category_converted',C,'Converted')]):
        y=1.18+i*1.23
        l.text(key+'.label',label,5.66,y-.25,2.36,.25,15.5,col,True)
        full=l.image(key,obs[key]['file'],(5.66,y,2.36,.8734),col)
        xx,yy,ww,hh=full['box'];iw,ih=obs[key]['size'];crop=(120,25,480,415)
        box=(xx+crop[0]/iw*ww,yy+crop[1]/ih*hh,(crop[2]-crop[0])/iw*ww,(crop[3]-crop[1])/ih*hh)
        l.rect(key+'.crop-back',box,None,'FFFFFF',1.5)
        l.rect(key+'.crop',box,None,MUTED,.6)
    # Two independent evaluations retain the Original/Converted correspondence.
    l.text('readout-title','2D readout',8.93,.97,1.30,.29,15.5,INK,True,'center')
    for i,(key,col,marker) in enumerate([('two_view_category_original',O,'circle'),('two_view_category_converted',C,'diamond')]):
        yy=1.6167+i*1.23
        l.rect('vlm-'+str(i),(8.28,yy-.225,.48,.45),'EEF3F9',LINE,.7,.06)
        l.text('vlm-label-'+str(i),'VLM',8.28,yy-.13,.48,.26,15.5,col,True,'center')
        point_panel(l,'readout-'+str(i),obs[key],(8.98,yy-.215,1.16,.43),col,marker)
        l.line('full-input-'+str(i),[(8.02,yy),(8.28,yy)],col,.9,True,
             meaning='Independent evaluation of the saved '+key+' input with the same model and query.',owners=('grounding','vlm'))
        l.line('full-readout-'+str(i),[(8.76,yy),(8.98,yy)],col,.9,True,
             meaning='Saved '+key+' point projected in the full image coordinate frame.',owners=('vlm','readout'))
    l.rect('target-key-box',(9.03,2.23,.12,.10),None,TARGET,.9)
    l.text('target-key','Target',9.25,2.17,.90,.26,15.5,TARGET)
    # Actual crossover inputs are supplementary probes; their outputs are not
    # substituted for the displayed full-condition readouts.
    l.text('probes-title','Region probes',10.32,.97,1.55,.29,15.5,INK,True,'center')
    for i,(key,label) in enumerate([('target_window_converted','Target swap'),('context_window_converted','Context swap')]):
        yy=1.62+i*1.11
        l.text(key+'.label',label,10.38,yy-.28,1.47,.26,15.5,MUTED,False,'center')
        detail=HERE/'assets'/f'{key}_detail.png';crop=(120,25,480,415)
        with Image.open(HERE/obs[key]['file']) as im:im.crop(crop).save(detail)
        image=l.image(key,str(detail.relative_to(HERE)),(10.42,yy,1.40,.74),LINE)
        x0,y0,x1,y1=obs[key]['bbox_xyxy_pixels'];iw,ih=crop[2]-crop[0],crop[3]-crop[1];xx,yy,ww,hh=image['box']
        l.rect(key+'.target',(xx+(x0-crop[0])/iw*ww,yy+(y0-crop[1])/ih*hh,(x1-x0)/iw*ww,(y1-y0)/ih*hh),None,TARGET,.9)
    l.text('crop-key','Gray box: probe detail',5.66,3.30,2.36,.26,15.5,MUTED)
    l.dot('prediction-key-dot',8.99,3.31,.035,O)
    l.dot('prediction-key-diamond',9.14,3.31,.035,C,'diamond')
    l.text('prediction-key','Prediction',9.26,3.18,.97,.26,15.5,MUTED)
    l.line('probe-separator',[(10.28,1.46),(10.28,3.43)],LINE,.65)
    # True excerpt pixels, split from independent qualitative end recordings.
    l.text('nav-title','Navigation',5.66,3.57,2.52,.31,18,C,True)
    l.text('map-type','Recorded map excerpts',8.31,3.61,3.43,.27,15.5,MUTED,False,'right')
    for key,label,col,x in [('original','Original',O,5.91),('nomdl','Converted',C,8.19)]:
        l.text('nav-'+key+'.label',label,x,3.97,1.75,.27,15.5,col,True,'center')
        l.image('nav-'+key,manifest['navigation'][key]['file'],(x,4.27,1.59,1.59),col)
    for y,label,col in [(4.56,'Executed','CC2525'),(5.04,'Reference','168A45')]:
        l.line('legend-'+label,[(10.18,y+.12),(10.43,y+.12)],col,2)
        l.text('legend-'+label+'.text',label,10.52,y,1.21,.26,15.5,MUTED)
    return l


def add_rect(slide,item):
    x,y,w,h=item['box'];kind=MSO_SHAPE.ROUNDED_RECTANGLE if item.get('radius') else MSO_SHAPE.RECTANGLE
    s=slide.shapes.add_shape(kind,Inches(x),Inches(y),Inches(w),Inches(h));s.name=item['id']
    if item.get('radius'):
        s.adjustments[0]=min(.15,item['radius']/min(w,h))
    if item.get('fill') is None:s.fill.background()
    else:s.fill.solid();s.fill.fore_color.rgb=rgb(item.get('fill','FFFFFF'))
    if item.get('stroke'):s.line.color.rgb=rgb(item['stroke']);s.line.width=Pt(item.get('lw',.7))
    else:s.line.fill.background()
    return s


def pptx_text(slide,it):
    x,y,w,h=it['box'];s=slide.shapes.add_textbox(Inches(x),Inches(y),Inches(w),Inches(h));s.name=it['id'];t=s.text_frame
    t.clear();t.word_wrap=False;t.auto_size=MSO_AUTO_SIZE.NONE
    t.margin_left=t.margin_right=t.margin_top=t.margin_bottom=0;t.vertical_anchor=MSO_ANCHOR.MIDDLE
    for i,line in enumerate(it['text'].split('\n')):
        p=t.paragraphs[0] if i==0 else t.add_paragraph();p.alignment={'left':PP_ALIGN.LEFT,'center':PP_ALIGN.CENTER,'right':PP_ALIGN.RIGHT}[it['align']]
        p.space_before=p.space_after=Pt(0);p.line_spacing=1.0
        r=p.add_run();r.text=line;r.font.name=FONTS[it['font']];r.font.size=Pt(it['size']);r.font.bold=it['bold'];r.font.color.rgb=rgb(it['color'])


def triangle(route,size=.065):
    (a,b),(x,y)=route[-2:];dx,dy=x-a,y-b;length=math.hypot(dx,dy);ux,uy=dx/length,dy/length
    return [(x,y),(x-size*ux-size*.48*uy,y-size*uy+size*.48*ux),(x-size*ux+size*.48*uy,y-size*uy-size*.48*ux)]


def pptx_line(slide,it):
    for i,(a,b) in enumerate(zip(it['points'],it['points'][1:])):
        if a==b:continue
        s=slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT,*[Inches(v) for v in (*a,*b)]);s.name=it['id']+f'.segment{i}'
        s.line.color.rgb=rgb(it['color']);s.line.width=Pt(it['lw'])
        if it.get('dash'):
            from pptx.enum.dml import MSO_LINE_DASH_STYLE
            s.line.dash_style=MSO_LINE_DASH_STYLE.DASH
    if it.get('head'):
        pts=triangle(it['points']);x0=min(p[0] for p in pts);y0=min(p[1] for p in pts)
        coords=[(round((x-x0)*10000),round((y-y0)*10000)) for x,y in pts]
        builder=slide.shapes.build_freeform(*coords[0],scale=Inches(1)/10000)
        builder.add_line_segments(coords[1:],close=True);s=builder.convert_to_shape(Inches(x0),Inches(y0));s.name=it['id']+'.head'
        s.fill.solid();s.fill.fore_color.rgb=rgb(it['color']);s.line.fill.background()


def neutralize(path):
    with tempfile.TemporaryDirectory() as temp:
        out=Path(temp)/'clean.pptx'
        with zipfile.ZipFile(path) as src,zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED) as dst:
            for info in src.infolist():
                b=src.read(info.filename)
                if info.filename.endswith('.xml'):
                    s=b.decode();s=re.sub(r'(<a:effectRef\b[^>]*\bidx=")[^"]+("[^>]*>)',r'\g<1>0\2',s);s=re.sub(r'<a:outerShdw\b[^>]*>.*?</a:outerShdw>','',s,flags=re.S);b=s.encode()
                dst.writestr(info,b)
        shutil.copy2(out,path)


def build_pptx(lay,path):
    prs=Presentation();prs.slide_width=Inches(W);prs.slide_height=Inches(H);s=prs.slides.add_slide(prs.slide_layouts[6]);s.background.fill.solid();s.background.fill.fore_color.rgb=rgb('FFFFFF')
    # Explicit z order: connectors -> images/cards -> foreground annotations/text.
    for it in lay.items:
        if it['kind']=='line' and not it.get('foreground'):pptx_line(s,it)
    for it in lay.items:
        k=it['kind']
        if k=='line':
            if it.get('foreground'):pptx_line(s,it)
            continue
        if k=='rect':add_rect(s,it)
        elif k=='image':
            x,y,w,h=it['box'];q=s.shapes.add_picture(str(HERE/it['path']),Inches(x),Inches(y),Inches(w),Inches(h));q.name=it['id']
            if it.get('stroke'):add_rect(s,{'id':it['id']+'.border','box':it['box'],'fill':None,'stroke':it['stroke'],'lw':it['lw']})
        elif k=='text':pptx_text(s,it)
        elif k=='dot':
            x,y,w,h=it['box'];q=s.shapes.add_shape(MSO_SHAPE.OVAL if it['shape']=='circle' else MSO_SHAPE.DIAMOND,Inches(x),Inches(y),Inches(w),Inches(h));q.name=it['id'];q.fill.solid();q.fill.fore_color.rgb=rgb(it['color']);q.line.color.rgb=rgb('FFFFFF');q.line.width=Pt(.4)
    prs.save(path);neutralize(path)


def svg(lay,path):
    scale=100
    s=[f'<svg xmlns="http://www.w3.org/2000/svg" width="3600" height="1800" viewBox="0 0 1200 600">','<rect width="1200" height="600" fill="white"/>']
    for it in sorted(lay.items,key=lambda z:0 if z['kind']=='line' and not z.get('foreground') else 1):
        k=it['kind'];ident=html.escape(it['id'])
        if k=='line':
            pts=' '.join(f'{x*scale:.4f},{y*scale:.4f}' for x,y in it['points']);dash=' stroke-dasharray="5 4"' if it.get('dash') else ''
            s.append(f'<polyline id="{ident}" points="{pts}" fill="none" stroke="#{it["color"]}" stroke-width="{it["lw"]*scale/72:.4f}"{dash}/>')
            if it.get('head'):s.append('<polygon points="'+' '.join(f'{x*scale:.4f},{y*scale:.4f}' for x,y in triangle(it['points']))+f'" fill="#{it["color"]}"/>')
            continue
        x,y,w,h=[v*scale for v in it['box']]
        if k in ('rect','image'):
            if k=='image':
                b=base64.b64encode((HERE/it['path']).read_bytes()).decode();s.append(f'<image id="{ident}" x="{x}" y="{y}" width="{w}" height="{h}" href="data:image/png;base64,{b}" preserveAspectRatio="xMidYMid meet"/>')
            if k=='rect' or it.get('stroke'):
                fill='none' if it.get('fill') is None or k=='image' else '#'+it['fill'];stroke='#'+it['stroke'] if it.get('stroke') else 'none'
                s.append(f'<rect id="{ident}-shape" x="{x}" y="{y}" width="{w}" height="{h}" rx="{it.get("radius",0)*scale}" fill="{fill}" stroke="{stroke}" stroke-width="{it.get("lw",.7)*scale/72}"/>')
        elif k=='text':
            fs=it['size']*scale/72;anchor={'left':'start','center':'middle','right':'end'}[it['align']];tx={'left':x,'center':x+w/2,'right':x+w}[it['align']]
            lines=it['text'].split('\n');base=y+h/2-(len(lines)-1)*fs*.5+fs*.34
            for i,line in enumerate(lines):s.append(f'<text id="{ident}-line{i}" x="{tx}" y="{base+i*fs}" text-anchor="{anchor}" font-family="{FONTS[it["font"]]}" font-size="{fs}" font-weight="{"bold" if it["bold"] else "normal"}" fill="#{it["color"]}">{html.escape(line)}</text>')
        elif k=='dot':
            if it['shape']=='circle':s.append(f'<ellipse id="{ident}" cx="{x+w/2}" cy="{y+h/2}" rx="{w/2}" ry="{h/2}" fill="#{it["color"]}" stroke="white" stroke-width=".55"/>')
            else:s.append(f'<polygon id="{ident}" points="{x+w/2},{y} {x+w},{y+h/2} {x+w/2},{y+h} {x},{y+h/2}" fill="#{it["color"]}" stroke="white" stroke-width=".55"/>')
    s.append('</svg>');path.write_text('\n'.join(s)+'\n')


def validate(lay):
    errors=[];boxes=[]
    for it in lay.items:
        if 'box' in it:
            x,y,w,h=it['box']
            if x<0 or y<0 or x+w>W+.001 or y+h>H+.001:errors.append(it['id']+': outside canvas')
        if it['kind']=='text':
            w,h=points(it['text'],it['size'],it['font'],it['bold'])
            if w>it['box'][2]+.02 or h>it['box'][3]+.03:errors.append(f"{it['id']}: text {w:.3f}x{h:.3f} exceeds {it['box'][2:]}")
            boxes.append(it)
    for i,a in enumerate(boxes):
        for b in boxes[i+1:]:
            x,y,w,h=a['box'];xx,yy,ww,hh=b['box']
            if min(x+w,xx+ww)>max(x,xx)+.008 and min(y+h,yy+hh)>max(y,yy)+.008:errors.append(a['id']+' overlaps '+b['id'])
    if errors:raise ValueError('\n'.join(errors))
    return {'text_bounds':'PASS','text_box_intersections':'PASS','text_count':len(boxes),'image_count':sum(i['kind']=='image' for i in lay.items),'minimum_font_pt':min(i['size'] for i in boxes),'font_sizes_pt':sorted({i['size'] for i in boxes}),'native_canvas_inches':[W,H],'paper_width_equivalent_min_pt':min(i['size'] for i in boxes)*5.5/W}


def specification(lay,variant):
    spec={'version':'1.0','mode':'inspired','title':'Structured reconstruction of hero A',
     'canvas':{'width':1200,'height':600,'background':'#FFFFFF'},
     'theme':{'font_family':'Liberation Sans','palette':{'original':'#'+O,'converted':'#'+C,'ink':'#'+INK}},
     'panels':[{'id':n,'x':x,'y':y,'width':w,'height':h,'title':t} for n,x,y,w,h,t in [
      ('materials',10,60,240,535,'Material rewrites'),('hub',275,160,255,395,'ConvertAsset'),
      ('grounding',555,60,248,286,'Paired grounding observations'),('probes',1035,90,155,255,'Region probes'),
      ('vlm',826,138,52,170,'Independent VLM evaluations'),('readout',890,90,135,250,'Spatial readout'),('navigation',555,355,632,240,'Navigation')]],
     'ports':lay.ports,'edges':lay.edges,
     'assets':[{'id':it['id'],'path':it['path'],'x':it['box'][0]*100,'y':it['box'][1]*100,'width':it['box'][2]*100,'height':it['box'][3]*100,'fit':'contain','alt':it['id']} for it in lay.items if it['kind']=='image'],
     'outputs':{'formats':['svg','pptx','pdf','png'],'basename':'hero_A_'+variant},
     'review':{'semantic_graph_approved':True,'approved_by':'user-approved design plan; lead checked against recorded input/output metadata','approved_at':'2026-09-15','notes':'Left pairs are material illustrations linked without causal arrowheads to the converter. Grounding and navigation use separate source scenes. Separate blue/orange paths preserve independent Original/Converted inputs and outputs. Region probes are actual extra crossover inputs shown as a side panel; their predictions do not replace the main readouts.'},
     'provenance':[{'id':'evidence','source':'evidence_manifest.json','status':'verified'},{'id':'layout-reference','source':'assets/reference_A.png','status':'user-provided'},{'id':'generated-hub','source':'assets/hub_prompt.txt','status':'user-provided','claim':'Explanatory 3D component only, not experimental evidence.'}]}
    return spec


def run(cmd):
    p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
    if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p.stdout


def render(pptx,pdf,png):
    with tempfile.TemporaryDirectory(prefix='hero-A-lo-') as td:
        temp=Path(td)
        run(['soffice','--headless',f'-env:UserInstallation=file://{temp}/profile','--convert-to','pdf:impress_pdf_Export:{"UseLosslessCompression":{"type":"boolean","value":"true"},"ReduceImageResolution":{"type":"boolean","value":"false"}}','--outdir',str(temp),str(pptx)])
        p=temp/(pptx.stem+'.pdf')
        if not p.exists():raise FileNotFoundError(p)
        run(['gs','-q','-sDEVICE=pdfwrite','-dCompatibilityLevel=1.5','-dNOPAUSE','-dBATCH','-dSAFER','-dAutoRotatePages=/None','-dDownsampleColorImages=false','-dDownsampleGrayImages=false',f'-sOutputFile={pdf}',str(p)])
    run(['pdftocairo','-png','-singlefile','-r','300',str(pdf),str(png.with_suffix(''))])


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['glass','vector','both'],default='glass');args=parser.parse_args()
    manifest=json.loads((HERE/'evidence_manifest.json').read_text());prep_hub()
    qa={}
    for variant in (['glass','vector'] if args.variant=='both' else [args.variant]):
        lay=build_layout(variant,manifest);qa[variant]=validate(lay)
        stem=HERE/('hero_A_'+variant)
        (stem.with_suffix('.layout.json')).write_text(json.dumps({'canvas_inches':[W,H],'items':lay.items,'allowed_text_image_overlays':lay.overlays},indent=2)+'\n')
        (stem.with_suffix('.spec.json')).write_text(json.dumps(specification(lay,variant),indent=2)+'\n')
        build_pptx(lay,stem.with_suffix('.pptx'));svg(lay,stem.with_suffix('.svg'));render(stem.with_suffix('.pptx'),stem.with_suffix('.pdf'),stem.with_suffix('.png'))
        qa[variant]['exports']={p.name:sha(p) for p in HERE.glob(stem.name+'.*') if p.suffix in ('.png','.pdf','.svg','.pptx')}
    detail_records=[]
    for key in ('target_window_converted','context_window_converted'):
        source=HERE/manifest['grounding'][key]['file'];detail=HERE/'assets'/f'{key}_detail.png'
        detail_records.append({'source':str(source.relative_to(HERE)),'source_sha256':sha(source),
                'crop_xyxy':[120,25,480,415],'output':str(detail.relative_to(HERE)),
                'output_sha256':sha(detail),'purpose':'Matching enlargement indicated by gray boxes in full observations'})
    (HERE/'assets/probe_detail_manifest.json').write_text(json.dumps({'crops':detail_records},indent=2)+'\n')
    (HERE/'geometry_qa.json').write_text(json.dumps(qa,indent=2)+'\n')
    print(json.dumps(qa,indent=2))

if __name__=='__main__':main()
