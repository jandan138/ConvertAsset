# AAAI 2027 Version Status

Template provenance: Official AAAI-27 author-kit files were downloaded from
`https://aaai.org/authorkit27/`, which redirects to
`https://aaai.org/wp-content/uploads/2026/05/AuthorKit27.zip`.

Author-kit SHA-256:
`e28c6ac9bc6eb3b4e2d849547d2cefb5162610ee39d0a12e0dc62d1126b44a7d`.

Installed local style files:

- `aaai2027.sty`: SHA-256
  `391bce82815bf698b8e382dd3ae7e30c75d7ab46df140cb295b1266016bc8623`
- `aaai2027.bst`: SHA-256
  `5db7765ba99de5c1e4686f9b3940a0add9c5e702f2164514462bec130ccb6e3c`

Readiness: primary AAAI candidate draft, buildable with the official 2027
style. The main body now uses AAAI-local sections synchronized from the
figure-driven ACL candidate story rather than the older tool-first shared
scaffold.

Local section overrides:

- `sections/abstract.tex`
- `sections/intro.tex`
- `sections/related.tex`
- `sections/method.tex`
- `sections/results.tex`
- `sections/discussion.tex`
- `sections/conclusion.tex`
- `sections/limitations.tex`
- `sections/ethical-considerations.tex`

Known missing checks: final AAAI page-limit policy, supplementary policy,
source-flattening or source-package requirements, reproducibility checklist
packaging, AI-use disclosure requirements, and a full page-by-page
AAAI-specific visual/readability review.

External status checked on 2026-06-02: the official AAAI conference page lists
AAAI-27 in Montréal, Québec, Canada, February 16-23, 2027, and links the
AAAI-27 author kit. The AAAI-27 public page also lists 2026-07-28 as the full
paper deadline.

Review-driven AAAI requirements: expand beyond four same-category furniture
assets, add downstream task validation or remove task-performance claims,
compare against official NVIDIA conversion/distillation tools, analyze
material-effect-specific degradation, validate practical guidelines at larger
scale, and expand GRScenes performance evidence beyond one scene and three
runs. The current VLM/InternNav/material-effect evidence package partially
addresses these risks, but final AAAI claims must remain bounded. See
`../../shared/evidence/reviews/2026-05-workshop-to-aaai27-revision-roadmap.md`.
