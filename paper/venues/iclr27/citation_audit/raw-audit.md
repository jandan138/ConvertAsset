# Citation Integrity Audit

Verdict: **FAIL**

| Metric | Count |
| --- | ---: |
| Unique cited keys | 18 |
| Citation occurrences | 21 |
| Identity pass | 9 |
| Support pass | 0 |
| Review required | 17 |
| Failures | 1 |

## References

| Key | Identity | Machine | Support occurrences |
| --- | --- | --- | ---: |
| `Anderson2018Vision` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Bai2025Qwen` | NOT_CHECKED | UNRESOLVED | 0/2 |
| `Bai2025Qwen3` | NOT_CHECKED | UNRESOLVED | 0/1 |
| `Chen2023Shikra` | NOT_CHECKED | DOI_UNVERIFIED | 0/1 |
| `Deitke2024Molmo` | VERIFIED_CROSS_INDEX | VERIFIED_CROSS_INDEX | 0/2 |
| `Geirhos2019Texture` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Google2026Gemma4` | NOT_CHECKED | UNRESOLVED | 0/1 |
| `Oquab2023DINOv2` | NOT_CHECKED | UNRESOLVED | 0/1 |
| `Radford2021Learning` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Tobin2017Domain` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Tremblay2018Training` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Wang2004Image` | METADATA_MISMATCH | METADATA_MISMATCH | 0/1 |
| `Wang2024GRUtopia` | NOT_CHECKED | DOI_UNVERIFIED | 0/1 |
| `Wei2026Ground` | NOT_CHECKED | UNRESOLVED | 0/1 |
| `You2024Ferret` | NOT_CHECKED | UNRESOLVED | 0/1 |
| `Zhang2018Unreasonable` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Zhao2021Calibrate` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/1 |
| `Zhu2025InternVL` | VERIFIED_PRIMARY | VERIFIED_PRIMARY | 0/2 |

## Findings

- REVIEW_REQUIRED `Anderson2018Vision`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Bai2025Qwen`: identity=NOT_CHECKED; support=['NOT_CHECKED', 'NOT_CHECKED']
- REVIEW_REQUIRED `Bai2025Qwen3`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Chen2023Shikra`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Deitke2024Molmo`: identity=VERIFIED_CROSS_INDEX; support=['NOT_CHECKED', 'NOT_CHECKED']
- REVIEW_REQUIRED `Geirhos2019Texture`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Google2026Gemma4`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Oquab2023DINOv2`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Radford2021Learning`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Tobin2017Domain`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Tremblay2018Training`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- FAIL `Wang2004Image`: identity=METADATA_MISMATCH; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Wang2024GRUtopia`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Wei2026Ground`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `You2024Ferret`: identity=NOT_CHECKED; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Zhang2018Unreasonable`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Zhao2021Calibrate`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED']
- REVIEW_REQUIRED `Zhu2025InternVL`: identity=VERIFIED_PRIMARY; support=['NOT_CHECKED', 'NOT_CHECKED']

Machine resolution narrows the review surface; it does not replace author verification of each cited claim.
