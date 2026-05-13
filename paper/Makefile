# Multi-venue LaTeX paper build system.
# Usage: make list | make aaai27 | make cvpr26 | make all | make clean | make template-check | make check

.RECIPEPREFIX := >

VENUES := aaai27 cvpr26
SHARED_DIR := shared
SHARED_SRCS := $(shell find $(SHARED_DIR) -type f \( -name '*.tex' -o -name '*.bib' -o -name '*.cls' -o -name '*.sty' -o -name '*.pdf' -o -name '*.png' -o -name '*.jpg' -o -name '*.jpeg' -o -name '*.yaml' -o -name '*.yml' \) -print 2>/dev/null)

.PHONY: all clean list template-check check check-latex-tools $(VENUES) $(addprefix clean-,$(VENUES)) $(addprefix check-template-,$(VENUES))

all: $(VENUES)

list:
> @printf 'Available venues: %s\n' '$(VENUES)'
> @printf 'Primary: aaai27\n'
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
> @if [ ! -f venues/aaai27/aaai27.sty ]; then \
>   echo 'Missing AAAI-27 style: expected venues/aaai27/aaai27.sty from the official AAAI-27 author kit.'; \
>   exit 1; \
> fi
> @if [ ! -f venues/aaai27/aaai27.bst ]; then \
>   echo 'Missing AAAI-27 bibliography style: expected venues/aaai27/aaai27.bst from the official AAAI-27 author kit.'; \
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

clean: $(addprefix clean-,$(VENUES))
> @rm -rf submissions arxiv-submission camera-ready

check:
> @for venue in $(VENUES); do \
>   echo "=== $$venue page/word diagnostics ==="; \
>   texcount -inc -total "venues/$$venue/main.tex" 2>/dev/null || echo 'texcount not installed'; \
>   echo ''; \
> done
