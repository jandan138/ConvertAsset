"""Build same-width before/after plates from the retained paper figure exports."""
from pathlib import Path
import hashlib
import json
import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image

HERE=Path(__file__).resolve().parent
VENUE=HERE.parent
sys.path.insert(0,str(VENUE/'scripts'))
import figure_style as style


def main():
    style.style()
    out=HERE/'comparison';out.mkdir(exist_ok=True)
    sources={}
    with PdfPages(out/'all_figures.pdf') as pdf:
        for name in ('overview','interventions','protocol','navigation','trajectories'):
            paths=[HERE/'round0'/f'{name}.png',VENUE/'figures'/f'{name}.png']
            ims=[Image.open(p).convert('RGB') for p in paths]
            heights=[im.height/im.width*5.5 for im in ims]
            height=max(heights)+.52
            fig=plt.figure(figsize=(11.55,height))
            for i,(im,h,label) in enumerate(zip(ims,heights,['Previous revision','Revised figure'])):
                x=.12+i*5.79
                fig.text(x/11.55,1-.06/height,label,fontsize=11,weight='bold',va='top',color=style.INK)
                ax=fig.add_axes([x/11.55,1-(.4+h)/height,5.5/11.55,h/height])
                ax.imshow(im,interpolation='none');ax.set_axis_off()
            fig.savefig(out/f'{name}.png',dpi=170)
            pdf.savefig(fig,dpi=300);plt.close(fig)
            sources[name]={str(p.relative_to(VENUE)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    (out/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')

if __name__=='__main__':main()
