# 2026-09-16 ICLR citation-integrity-auditor 复检

按 `/root/.cursor/skills/citation-integrity-auditor/SKILL.md` 对
`paper/venues/iclr27/main.tex` + `references.bib` 做全量盘点，不抽样。

## 官方脚本

```bash
python paper/venues/iclr27/citation_audit/run_audit.py \
  --main-tex paper/venues/iclr27/main.tex \
  --bib paper/venues/iclr27/references.bib \
  --support-ledger paper/venues/iclr27/citation_audit/human-support.json \
  --cache paper/venues/iclr27/citation_audit/normalized-metadata-cache.json \
  --json-out /tmp/iclr-citation-audit-20260916.json \
  --markdown-out /tmp/iclr-citation-audit-20260916.md \
  --project-root . --offline --strict
```

退出码 **1**，判定 **REVIEW_REQUIRED**。18 个 cited key，21 处语境；机器 identity
10 通过、8 未解析；support 0/21；**failures 0**。未改 BibTeX。

## 本次独立身份核验

对声明 DOI 走 Crossref 或 DataCite；其余走 arXiv、CVF、PMLR、ICLR
proceedings、Gemma 模型卡。未发现 DOI 指向另一篇论文，也未在已查记录中看到
retraction。机器未解析的 8 条均能落到同名作品，不是不存在。

DualVLN 的 arXiv PDF 标题含 *Vision-and-Language*，ICLR 2026 proceedings /
OpenReview 标题为 *Vision-Language*。BibTeX 保留 PDF 形式；同一作者与论坛。

## 门控

Skill 要求作者对每条语境签字后才能 `PASS`。现有
`human-support.json` 仍全部 `NOT_CHECKED`。顾问阅读见
`citation_audit/advisory-support.json`，不能代替签字。
