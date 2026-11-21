# Multi-venue LaTeX paper build system.
# Usage: make iclr27 | make iclr27-check | make iclr27-stage | make list

.RECIPEPREFIX := >

.DEFAULT_GOAL := iclr27
VENUES := iclr27 aaai27 acl27 cvpr26
ANALYSIS_PYTHON ?= python
SHARED_DIR := shared
SHARED_SRCS := $(shell find $(SHARED_DIR) -type f \( -name '*.tex' -o -name '*.bib' -o -name '*.cls' -o -name '*.sty' -o -name '*.pdf' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.yaml' -o -name '*.yml' \) -print 2>/dev/null)

.PHONY: all clean list template-check check check-latex-tools acl27-supplement clean-acl27-supplement $(VENUES) $(addprefix clean-,$(VENUES)) $(addprefix check-template-,$(VENUES))

all: $(VENUES)

list:
> @printf 'Available venues: %s\n' '$(VENUES)'
> @printf 'Primary: iclr27 (model behavior, visual grounding, navigation)\n'
> @printf 'Earlier venue wrappers: aaai27, acl27\n'
> @printf 'Historical baseline: cvpr26\n'

template-check: check-latex-tools $(addprefix check-template-,$(VENUES))
> @echo 'Template check complete.'

check-latex-tools:
> @if ! command -v latexmk >/dev/null 2>&1; then \
>   if ! command -v pdflatex >/dev/null 2>&1 || ! command -v bibtex >/dev/null 2>&1; then \
>     echo 'Missing LaTeX build tooling: install latexmk, or install both pdflatex and bibtex for fallback.'; \
>     exit 1; \
>   fi; \
> fi

check-template-aaai27:
> @if [ ! -f venues/aaai27/aaai2027.sty ]; then \
>   echo 'Missing AAAI-27 style: expected venues/aaai27/aaai2027.sty from the official AAAI-27 author kit.'; \
>   exit 1; \
> fi
> @if [ ! -f venues/aaai27/aaai2027.bst ]; then \
>   echo 'Missing AAAI-27 bibliography style: expected venues/aaai27/aaai2027.bst from the official AAAI-27 author kit.'; \
>   exit 1; \
> fi

check-template-acl27:
> @if [ ! -f venues/acl27/acl.sty ]; then \
>   echo 'Missing ACL style: expected venues/acl27/acl.sty from the official ACL style files.'; \
>   exit 1; \
> fi
> @if [ ! -f venues/acl27/acl_natbib.bst ]; then \
>   echo 'Missing ACL bibliography style: expected venues/acl27/acl_natbib.bst from the official ACL style files.'; \
>   exit 1; \
> fi

check-template-cvpr26:
> @if [ ! -f venues/cvpr26/cvpr.sty ]; then \
>   echo 'Missing CVPR style: expected venues/cvpr26/cvpr.sty'; \
>   exit 1; \
> fi

> @if [ ! -f venues/cvpr26/ieeenat_fullname.bst ]; then \
>   echo 'Missing CVPR bibliography style: expected venues/cvpr26/ieeenat_fullname.bst'; \
>   exit 1; \
> fi

check-template-iclr27:
> @test -f venues/iclr27/iclr2027_conference.sty -a -f venues/iclr27/iclr2027_conference.bst || { echo 'Run python venues/iclr27/scripts/fetch_template.py'; exit 1; }

define VENUE_RULE
$(1)_MAIN := venues/$(1)/main.tex
$(1)_LOCAL := $(shell find venues/$(1) -type f \( -name '*.tex' -o -name '*.sty' -o -name '*.cls' -o -name '*.bib' -o -name '*.bst' -o -name '.latexmkrc' -o -name 'STATUS.md' \) -print 2>/dev/null)
$(1)_PDF := venues/$(1)/build/main.pdf
$(1)_BUILDDIR := venues/$(1)/build

$$($(1)_PDF): $$($(1)_MAIN) $$($(1)_LOCAL) $(SHARED_SRCS) | $$($(1)_BUILDDIR)
> @$$(MAKE) check-latex-tools
> @$$(MAKE) check-template-$(1)
> @if command -v latexmk >/dev/null 2>&1; then cd venues/$(1) && latexmk -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error main.tex; else cd venues/$(1) && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex && BIBINPUTS="../../shared:" bibtex build/main && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex; fi

$$($(1)_BUILDDIR):
> @mkdir -p $$@

$(1): $$($(1)_PDF)
> @echo '=== $(1) built: $$($(1)_PDF) ==='

clean-$(1):
> @cd venues/$(1) && latexmk -C -outdir=build 2>/dev/null || true
> @rm -rf $$($(1)_BUILDDIR)
endef

$(foreach v,$(VENUES),$(eval $(call VENUE_RULE,$(v))))

.PHONY: iclr27-assets iclr27-check iclr27-stage
iclr27-assets:
> $(ANALYSIS_PYTHON) shared/evidence/experiments/11_iclr_model_behavior/analyze.py --new-runs shared/evidence/raw/iclr_model_behavior/runs_clean_v2
> $(ANALYSIS_PYTHON) venues/iclr27/scripts/build_assets.py

venues/iclr27/build/main.pdf: iclr27-assets

iclr27-check: iclr27
> $(ANALYSIS_PYTHON) venues/iclr27/scripts/check_submission.py

iclr27-stage: iclr27-check
> $(ANALYSIS_PYTHON) venues/iclr27/scripts/stage_submission.py

ACL27_SUPPLEMENT := venues/acl27/supplement.tex
ACL27_SUPPLEMENT_PDF := venues/acl27/build/supplement.pdf
ACL27_SUPPLEMENT_LOCAL := $(shell find venues/acl27 -type f \( -name '*.tex' -o -name '*.sty' -o -name '*.cls' -o -name '*.bib' -o -name '*.bst' -o -name '.latexmkrc' -o -name 'STATUS.md' \) -print 2>/dev/null)

$(ACL27_SUPPLEMENT_PDF): $(ACL27_SUPPLEMENT) $(ACL27_SUPPLEMENT_LOCAL) $(SHARED_SRCS) | venues/acl27/build
> @$(MAKE) check-latex-tools
> @$(MAKE) check-template-acl27
> @if command -v latexmk >/dev/null 2>&1; then cd venues/acl27 && latexmk -cd -pdf -outdir=build -interaction=nonstopmode -halt-on-error supplement.tex; else cd venues/acl27 && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build supplement.tex && BIBINPUTS="../../shared:" bibtex build/supplement && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build supplement.tex && pdflatex -interaction=nonstopmode -halt-on-error -output-directory=build supplement.tex; fi

acl27-supplement: $(ACL27_SUPPLEMENT_PDF)
> @echo '=== acl27 supplement built: $(ACL27_SUPPLEMENT_PDF) ==='

clean-acl27-supplement:
> @cd venues/acl27 && latexmk -C -outdir=build supplement.tex 2>/dev/null || true
> @rm -f venues/acl27/build/supplement.*

clean: $(addprefix clean-,$(VENUES))
> @rm -rf submissions arxiv-submission camera-ready

check:
> @for venue in $(VENUES); do \
>   echo "=== $$venue page/word diagnostics ==="; \
>   texcount -inc -total "venues/$$venue/main.tex" 2>/dev/null || echo 'texcount not installed'; \
>   echo ''; \
> done
