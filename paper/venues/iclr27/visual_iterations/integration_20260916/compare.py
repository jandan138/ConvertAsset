"""Create a review-only comparison booklet from existing figure exports."""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from PIL import Image
ROOT=next(p for p in Path(__file__).resolve().parents if (p/"CLAUDE.md").exists())
HERE=Path(__file__).resolve().parent
SHARED=ROOT/"paper/shared/figures"
VENUE=ROOT/"paper/venues/iclr27"
PAIRS=[("System overview",SHARED/"tmp/hero_candidate_A_system.png",VENUE/"figures/system_hero.png"),("Material comparison",SHARED/"fig_material_effect_baseline_qualitative_v3.png",VENUE/"figures/supplement/appendix_material_comparison.png"),("Scene context",SHARED/"fig_render_scene_evidence_wide_v3.png",VENUE/"figures/supplement/appendix_scene_pairs.png"),("Navigation layout",SHARED/"fig_internnav_rollout_main_v4.png",VENUE/"figures/supplement/appendix_navigation_cases_04.png")]
with PdfPages(HERE/"before_after.pdf") as pdf:
 for title,old,new in PAIRS:
  fig,axes=plt.subplots(1,2,figsize=(12,9));fig.suptitle(title,fontsize=16)
  for ax,path,label in zip(axes,[old,new],["Earlier figure","Integrated figure"]):
   ax.imshow(Image.open(path));ax.set_title(label);ax.axis("off")
  fig.tight_layout();pdf.savefig(fig);plt.close(fig)
with PdfPages(HERE/"figure_gallery.pdf") as pdf:
 for path in [VENUE/"figures/system_hero.png",*sorted((VENUE/"figures/supplement").glob("appendix_*.png"))]:
  fig,ax=plt.subplots(figsize=(7,9));ax.imshow(Image.open(path));ax.axis("off");fig.tight_layout();pdf.savefig(fig);plt.close(fig)
print(HERE/"before_after.pdf")
