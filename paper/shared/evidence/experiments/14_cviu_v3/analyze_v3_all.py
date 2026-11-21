#!/usr/bin/env python3
"""Analyze all CVIU v3 results: scaling/families, variance hierarchy, optical mechanisms, and risk gate."""

from __future__ import annotations

import argparse
from collections import defaultdict
import itertools
import json
from pathlib import Path
import sys
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from optical_and_risk_features import DEPLOY_AUTO_FEATURES, FEATURE_NAMES_ALL  # noqa: E402
from v3_common import (  # noqa: E402
    average_precision_np,
    fit_standardized_l2_logreg,
    parse_point_by_mode,
    point_displacement_px,
    predict_proba_logreg,
    repo_root_from_script,
    roc_auc_score_np,
    scene_cluster_diff_ci,
    scene_cluster_ratio_ci,
    score_normalized_point,
)


C_GRID: tuple[float, ...] = (0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
GEOM_FEATURES: tuple[str, ...] = ("log_area_frac", "aspect_ratio", "center_dist_norm", "border_touch", "mask_iou")
PIXEL_ONLY_FEATURES: tuple[str, ...] = tuple(
    f for f in DEPLOY_AUTO_FEATURES if f not in GEOM_FEATURES and not f.startswith("cat_is_")
)


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _index_oc_predictions(rows: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    idx: dict[tuple[str, str], dict[str, Any]] = {}
    for r in rows:
        if r.get("status") != "ok":
            continue
        idx[(str(r["pair_id"]), str(r["condition"]))] = r
    return idx


def _summarize_model_oc(
    *,
    pair_rows: list[dict[str, Any]],
    pred_idx: dict[tuple[str, str], dict[str, Any]],
    scene_pos: dict[str, int],
    draws: np.ndarray,
) -> tuple[dict[str, Any], dict[str, np.ndarray]]:
    n_scenes = len(scene_pos)
    mat: dict[str, np.ndarray] = defaultdict(lambda: np.zeros((n_scenes, 2), dtype=np.float64))
    for metric in (
        "original_hit_rate",
        "converted_hit_rate",
        "hit_rate_difference",
        "loss_rate",
        "gain_rate",
        "flip_rate",
        "loss_given_original_success",
        "gain_given_original_failure",
        "original_valid_point_rate",
        "converted_valid_point_rate",
        "cross_condition_point_displacement_px",
    ):
        _ = mat[metric]

    for ref in pair_rows:
        pid = ref["pair_id"]
        sid = ref["scene_id"]
        si = scene_pos[sid]
        a = pred_idx.get((pid, "original"))
        b = pred_idx.get((pid, "converted"))
        if a is None or b is None:
            continue
        ah = int(bool(a["hit"]))
        bh = int(bool(b["hit"]))
        loss = int(ah == 1 and bh == 0)
        gain = int(ah == 0 and bh == 1)
        mat["original_hit_rate"][si] += (ah, 1.0)
        mat["converted_hit_rate"][si] += (bh, 1.0)
        mat["hit_rate_difference"][si] += (bh - ah, 1.0)
        mat["loss_rate"][si] += (loss, 1.0)
        mat["gain_rate"][si] += (gain, 1.0)
        mat["flip_rate"][si] += (int(ah != bh), 1.0)
        mat["loss_given_original_success"][si] += (loss, float(ah))
        mat["gain_given_original_failure"][si] += (gain, float(1 - ah))
        mat["original_valid_point_rate"][si] += (int(bool(a["valid_point"])), 1.0)
        mat["converted_valid_point_rate"][si] += (int(bool(b["valid_point"])), 1.0)
        shift = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
        if shift is not None:
            mat["cross_condition_point_displacement_px"][si] += (shift, 1.0)

    metrics = {k: scene_cluster_ratio_ci(v, draws) for k, v in mat.items()}
    return {"metrics": metrics}, dict(mat)


def analyze_scaling_and_families(
    *,
    orig_pairs: list[dict[str, Any]],
    scene_pos: dict[str, int],
    draws: np.ndarray,
    v1_runs_dir: Path,
    v3_runs_dir: Path,
) -> dict[str, Any]:
    model_runs: dict[str, dict[str, Any]] = {}
    raw_mats: dict[str, dict[str, np.ndarray]] = {}

    candidates: list[tuple[str, str, str, Path]] = []
    for short, label, family in (
        ("8b", "Qwen/Qwen3-VL-8B-Instruct", "Qwen3-VL"),
        ("32b", "Qwen/Qwen3-VL-32B-Instruct", "Qwen3-VL"),
    ):
        p = v1_runs_dir / short / "formal_repeat0" / "predictions.jsonl"
        if p.is_file():
            candidates.append((f"qwen3_vl_{short}_r0", label, family, p))

    if v3_runs_dir.is_dir():
        for folder in sorted(v3_runs_dir.glob("formal_*")):
            comp = folder / "completion.json"
            pred = folder / "predictions.jsonl"
            meta_p = folder / "metadata.json"
            if comp.is_file() and pred.is_file():
                c_data = json.loads(comp.read_text(encoding="utf-8"))
                if c_data.get("status") != "complete":
                    continue
                meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.is_file() else {}
                mkey = meta.get("model_key", folder.name.replace("formal_", "", 1))
                candidates.append((mkey, meta.get("hf_repo", mkey), meta.get("family", "Unknown"), pred))

    model_indices: dict[str, dict[tuple[str, str], dict[str, Any]]] = {}
    for mkey, hf_repo, family, pred_path in candidates:
        rows = _read_jsonl(pred_path)
        idx = _index_oc_predictions(rows)
        model_indices[mkey] = idx
        summary, raw_m = _summarize_model_oc(pair_rows=orig_pairs, pred_idx=idx, scene_pos=scene_pos, draws=draws)
        summary.update({"hf_repo": hf_repo, "family": family, "predictions_loaded": len(rows)})
        model_runs[mkey] = summary
        raw_mats[mkey] = raw_m

    contrasts: dict[str, Any] = {}
    pairs_to_compare = [
        ("qwen3_vl_32b_r0", "qwen3_vl_8b_r0"),
        ("qwen3_vl_8b_r0", "qwen3_vl_2b"),
        ("qwen3_vl_32b_r0", "qwen3_vl_2b"),
    ]
    for other in (
        "internvl3_5_8b",
        "internvl3_5_14b",
        "internvl3_5_38b",
        "molmo2_8b",
        "pixtral_12b",
        "llava_next_mistral_7b",
        "molmo_7b_o",
    ):
        if other in raw_mats and "qwen3_vl_8b_r0" in raw_mats:
            pairs_to_compare.append((other, "qwen3_vl_8b_r0"))
        if other in raw_mats and "qwen3_vl_32b_r0" in raw_mats:
            pairs_to_compare.append((other, "qwen3_vl_32b_r0"))

    for mb, ma in pairs_to_compare:
        if mb in raw_mats and ma in raw_mats:
            cname = f"{mb}__minus__{ma}"
            contrasts[cname] = {
                m: scene_cluster_diff_ci(raw_mats[mb][m], raw_mats[ma][m], draws)
                for m in ("original_hit_rate", "converted_hit_rate", "flip_rate", "loss_rate", "gain_rate", "cross_condition_point_displacement_px")
            }

    fam_4x8b = [k for k in ("qwen3_vl_8b_r0", "internvl3_5_8b", "molmo2_8b", "llava_next_mistral_7b") if k in model_indices]
    overlap_4x8b: dict[str, Any] = {"models": fam_4x8b, "pair_count": len(orig_pairs)}
    if fam_4x8b:
        loss_hist: dict[str, int] = {str(k): 0 for k in range(len(fam_4x8b) + 1)}
        gain_hist: dict[str, int] = {str(k): 0 for k in range(len(fam_4x8b) + 1)}
        flip_hist: dict[str, int] = {str(k): 0 for k in range(len(fam_4x8b) + 1)}
        for ref in orig_pairs:
            pid = ref["pair_id"]
            n_lo = n_ga = n_fl = 0
            for mk in fam_4x8b:
                a = model_indices[mk].get((pid, "original"))
                b = model_indices[mk].get((pid, "converted"))
                if a is None or b is None:
                    continue
                ah, bh = int(bool(a["hit"])), int(bool(b["hit"]))
                n_lo += int(ah == 1 and bh == 0)
                n_ga += int(ah == 0 and bh == 1)
                n_fl += int(ah != bh)
            loss_hist[str(n_lo)] += 1
            gain_hist[str(n_ga)] += 1
            flip_hist[str(n_fl)] += 1
        any_loss = sum(v for k, v in loss_hist.items() if int(k) >= 1)
        single_loss = loss_hist.get("1", 0)
        overlap_4x8b["loss_count_histogram"] = loss_hist
        overlap_4x8b["gain_count_histogram"] = gain_hist
        overlap_4x8b["flip_count_histogram"] = flip_hist
        overlap_4x8b["any_loss_pairs"] = any_loss
        overlap_4x8b["single_family_only_share_of_losses"] = (single_loss / any_loss) if any_loss else 0.0

    return {
        "pair_count": len(orig_pairs),
        "scene_count": len(scene_pos),
        "bootstrap": {"unit": "scene", "draws": int(len(draws)), "seed": 20261114},
        "models": model_runs,
        "contrasts": contrasts,
        "family_overlap_4x8b": overlap_4x8b,
    }


def analyze_variance_decomposition(
    *,
    orig_pairs: list[dict[str, Any]],
    control_scene_ids: list[str],
    v1_runs_dir: Path,
    render_controls_path: Path,
    v3_runs_dir: Path,
) -> dict[str, Any]:
    ctrl_set = set(control_scene_ids)
    ctrl_pairs = [r for r in orig_pairs if r["scene_id"] in ctrl_set]

    out: dict[str, Any] = {
        "control_scenes": control_scene_ids,
        "pair_count": len(ctrl_pairs),
        "input_count": len(ctrl_pairs) * 2,
    }

    # Level 1: Greedy repeat determinism across 3 formal processes
    greedy_summary: dict[str, Any] = {}
    for m in ("8b", "32b"):
        rep_idxs = {}
        for rep in range(3):
            p = v1_runs_dir / m / f"formal_repeat{rep}" / "predictions.jsonl"
            if p.is_file():
                rep_idxs[rep] = _index_oc_predictions(_read_jsonl(p))
        if len(rep_idxs) == 3:
            disagree = 0
            total = 0
            shifts = []
            for r in ctrl_pairs:
                for cond in ("original", "converted"):
                    for i, j in itertools.combinations(range(3), 2):
                        a, b = rep_idxs[i][(r["pair_id"], cond)], rep_idxs[j][(r["pair_id"], cond)]
                        disagree += int(bool(a["hit"]) != bool(b["hit"]))
                        total += 1
                        s = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
                        if s is not None:
                            shifts.append(s)
            greedy_summary[m] = {
                "pairwise_comparisons": total,
                "pairwise_hit_disagreement_rate": disagree / max(total, 1),
                "mean_point_displacement_px": float(np.mean(shifts)) if shifts else 0.0,
            }

    # Level 1: Greedy repeat determinism across v1 (8b/32b) and all v3 formal + control_repeat_* pairs
    if v3_runs_dir.is_dir():
        for cr_dir in sorted(v3_runs_dir.glob("control_repeat_*")):
            mkey = cr_dir.name.replace("control_repeat_", "", 1)
            f_path = v3_runs_dir / f"formal_{mkey}" / "predictions.jsonl"
            cr_path = cr_dir / "predictions.jsonl"
            if not (f_path.is_file() and cr_path.is_file()):
                continue
            i0 = _index_oc_predictions(_read_jsonl(f_path))
            i1 = _index_oc_predictions(_read_jsonl(cr_path))
            dis, tot, sh = 0, 0, []
            for r in ctrl_pairs:
                for cond in ("original", "converted"):
                    a, b = i0.get((r["pair_id"], cond)), i1.get((r["pair_id"], cond))
                    if a is None or b is None:
                        continue
                    dis += int(bool(a["hit"]) != bool(b["hit"]))
                    tot += 1
                    s = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
                    if s is not None:
                        sh.append(s)
            greedy_summary[mkey] = {
                "pairwise_comparisons": tot,
                "pairwise_hit_disagreement_rate": dis / max(tot, 1),
                "mean_point_displacement_px": float(np.mean(sh)) if sh else 0.0,
            }
    out["level1_greedy_process_repeat"] = greedy_summary

    # Level 2: Stochastic decoding variance
    stoch_path = v3_runs_dir / "stochastic_control_qwen3_vl_8b" / "predictions.jsonl"
    if stoch_path.is_file():
        by_inp: dict[tuple[str, str], dict[int, dict[str, Any]]] = defaultdict(dict)
        for row in _read_jsonl(stoch_path):
            if row.get("status") == "ok":
                by_inp[(str(row["pair_id"]), str(row["condition"]))][int(row["draw_idx"])] = row
        pw_dis = 0
        pw_tot = 0
        any_flip_inputs = 0
        raw_changed = 0
        shifts = []
        valid_inputs = 0
        for key, draws_map in sorted(by_inp.items()):
            dkeys = sorted(draws_map)
            if len(dkeys) < 2:
                continue
            valid_inputs += 1
            hits = {bool(draws_map[d]["hit"]) for d in dkeys}
            if len(hits) > 1:
                any_flip_inputs += 1
            for d1, d2 in itertools.combinations(dkeys, 2):
                a, b = draws_map[d1], draws_map[d2]
                pw_dis += int(bool(a["hit"]) != bool(b["hit"]))
                raw_changed += int(a["raw_response"] != b["raw_response"])
                pw_tot += 1
                s = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
                if s is not None:
                    shifts.append(s)
        out["level2_stochastic_decoding_8b_t02"] = {
            "inputs_evaluated": valid_inputs,
            "pairwise_comparisons": pw_tot,
            "pairwise_hit_disagreement_rate": pw_dis / max(pw_tot, 1),
            "inputs_with_any_flip_rate": any_flip_inputs / max(valid_inputs, 1),
            "pairwise_raw_response_change_rate": raw_changed / max(pw_tot, 1),
            "mean_point_displacement_px": float(np.mean(shifts)) if shifts else None,
        }

    # Level 3: Ray-tracing re-render noise from v1 render_controls.json + v3 control_rerender_* runs
    l3: dict[str, Any] = {}
    if render_controls_path.is_file():
        rc = json.loads(render_controls_path.read_text(encoding="utf-8"))
        for m in ("8b", "32b"):
            agg = rc["models"][m]["same_condition_render_repeat_all"]
            l3[m] = {
                "n_inputs": agg["n"],
                "hit_flips": agg["hit_flip"],
                "hit_flip_rate": agg["hit_flip"] / max(agg["n"], 1),
                "mean_point_displacement_px": agg["mean_point_displacement_px"],
            }
    if v3_runs_dir.is_dir():
        for rr_dir in sorted(v3_runs_dir.glob("control_rerender_*")):
            mkey = rr_dir.name.replace("control_rerender_", "", 1)
            f_path = v3_runs_dir / f"formal_{mkey}" / "predictions.jsonl"
            rr_path = rr_dir / "predictions.jsonl"
            if not (f_path.is_file() and rr_path.is_file()):
                continue
            idx_f = _index_oc_predictions(_read_jsonl(f_path))
            idx_rr = _index_oc_predictions(_read_jsonl(rr_path))
            flips, tot, raw_chg, shifts = 0, 0, 0, []
            for r in ctrl_pairs:
                for cond in ("original", "converted"):
                    a, b = idx_f.get((r["pair_id"], cond)), idx_rr.get((r["pair_id"], cond))
                    if a is None or b is None:
                        continue
                    flips += int(bool(a["hit"]) != bool(b["hit"]))
                    raw_chg += int(a.get("raw_response") != b.get("raw_response"))
                    tot += 1
                    s = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
                    if s is not None:
                        shifts.append(s)
            if tot > 0:
                l3[mkey] = {
                    "n_inputs": tot,
                    "hit_flips": flips,
                    "hit_flip_rate": flips / max(tot, 1),
                    "raw_response_change_rate": raw_chg / max(tot, 1),
                    "mean_point_displacement_px": float(np.mean(shifts)) if shifts else None,
                }
    if l3:
        out["level3_raytracing_rerender"] = l3

    # Level 4: Material conversion on identical 48 control pairs (v1 + all completed v3 models)
    l4_candidates: list[tuple[str, Path]] = [
        (m, v1_runs_dir / m / "formal_repeat0" / "predictions.jsonl") for m in ("8b", "32b")
    ]
    if v3_runs_dir.is_dir():
        for f_dir in sorted(v3_runs_dir.glob("formal_*")):
            mkey = f_dir.name.replace("formal_", "", 1)
            l4_candidates.append((mkey, f_dir / "predictions.jsonl"))
    l4 = {}
    for m, p in l4_candidates:
        if p.is_file():
            idx = _index_oc_predictions(_read_jsonl(p))
            flips, losses, gains, shifts, tot_p = 0, 0, 0, [], 0
            for r in ctrl_pairs:
                a, b = idx.get((r["pair_id"], "original")), idx.get((r["pair_id"], "converted"))
                if a is None or b is None:
                    continue
                tot_p += 1
                ah, bh = bool(a["hit"]), bool(b["hit"])
                flips += int(ah != bh)
                losses += int(ah and not bh)
                gains += int(not ah and bh)
                s = point_displacement_px(a.get("point_normalized"), bool(a.get("valid_point")), b.get("point_normalized"), bool(b.get("valid_point")))
                if s is not None:
                    shifts.append(s)
            if tot_p > 0:
                l4[m] = {
                    "pairs": tot_p,
                    "flips": flips,
                    "flip_rate": flips / max(tot_p, 1),
                    "losses": losses,
                    "gains": gains,
                    "mean_point_displacement_px": float(np.mean(shifts)) if shifts else None,
                }
    out["level4_material_conversion_on_control_pairs"] = l4
    return out


def analyze_optical_mechanisms(
    *,
    orig_pairs: list[dict[str, Any]],
    scene_pos: dict[str, int],
    draws: np.ndarray,
    features_by_pair: dict[str, dict[str, Any]],
    v1_runs_dir: Path,
    v3_runs_dir: Path,
) -> dict[str, Any]:
    cf_candidates: list[tuple[str, Path, Path]] = []
    p8_path = v1_runs_dir / "8b" / "formal_repeat0" / "predictions.jsonl"
    cf8_path = v3_runs_dir / "counterfactual_qwen3_vl_8b" / "predictions.jsonl"
    if p8_path.is_file() and cf8_path.is_file():
        cf_candidates.append(("qwen3_vl_8b", p8_path, cf8_path))

    if v3_runs_dir.is_dir():
        for cf_dir in sorted(v3_runs_dir.glob("counterfactual_*")):
            mkey = cf_dir.name.replace("counterfactual_", "", 1)
            if mkey == "qwen3_vl_8b":
                continue
            comp_p = cf_dir / "completion.json"
            if comp_p.is_file() and json.loads(comp_p.read_text(encoding="utf-8")).get("status") != "complete":
                continue
            f_path = v3_runs_dir / f"formal_{mkey}" / "predictions.jsonl"
            cf_p = cf_dir / "predictions.jsonl"
            if f_path.is_file() and cf_p.is_file():
                cf_candidates.append((mkey, f_path, cf_p))

    if not cf_candidates:
        return {"status": "pending_counterfactual_predictions"}

    exact_mask_pairs = [r for r in orig_pairs if features_by_pair[r["pair_id"]]["mask_iou"] > 0.999999]

    def _analyze_one_cf_model(oc_path: Path, cf_path: Path) -> dict[str, Any]:
        idx_oc = _index_oc_predictions(_read_jsonl(oc_path))
        idx_cf = _index_oc_predictions(_read_jsonl(cf_path))

        def _subset_report(subset_pairs: list[dict[str, Any]], label: str) -> dict[str, Any]:
            n_s = len(scene_pos)
            cond_hit: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("O", "T", "B", "F", "photo")}
            cond_val: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("O", "T", "B", "F", "photo")}
            flips_vs_o: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("T", "B", "F", "photo")}
            gains_vs_o: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("T", "B", "F", "photo")}
            losses_vs_o: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("T", "B", "F", "photo")}
            disp_vs_o: dict[str, np.ndarray] = {c: np.zeros((n_s, 2), dtype=np.float64) for c in ("T", "B", "F", "photo")}
            fac_mats: dict[str, np.ndarray] = {k: np.zeros((n_s, 2), dtype=np.float64) for k in ("T_minus_O", "B_minus_O", "F_minus_O", "interaction_F_minus_T_minus_B_plus_O")}

            for r in subset_pairs:
                pid = r["pair_id"]
                si = scene_pos[r["scene_id"]]
                row_map = {
                    "O": idx_oc.get((pid, "original")),
                    "F": idx_oc.get((pid, "converted")),
                    "T": idx_cf.get((pid, "target_only")),
                    "B": idx_cf.get((pid, "background_only")),
                    "photo": idx_cf.get((pid, "photometric_matched")),
                }
                if any(v is None for v in row_map.values()):
                    continue
                ho = int(bool(row_map["O"]["hit"]))
                ht = int(bool(row_map["T"]["hit"]))
                hb = int(bool(row_map["B"]["hit"]))
                hf = int(bool(row_map["F"]["hit"]))

                for ck, rv in row_map.items():
                    cond_hit[ck][si] += (int(bool(rv["hit"])), 1.0)
                    cond_val[ck][si] += (int(bool(rv["valid_point"])), 1.0)
                    if ck != "O":
                        hc = int(bool(rv["hit"]))
                        flips_vs_o[ck][si] += (int(hc != ho), 1.0)
                        gains_vs_o[ck][si] += (int(ho == 0 and hc == 1), 1.0)
                        losses_vs_o[ck][si] += (int(ho == 1 and hc == 0), 1.0)
                        sh = point_displacement_px(
                            row_map["O"].get("point_normalized"),
                            bool(row_map["O"].get("valid_point")),
                            rv.get("point_normalized"),
                            bool(rv.get("valid_point")),
                        )
                        if sh is not None:
                            disp_vs_o[ck][si] += (sh, 1.0)

                fac_mats["T_minus_O"][si] += (ht - ho, 1.0)
                fac_mats["B_minus_O"][si] += (hb - ho, 1.0)
                fac_mats["F_minus_O"][si] += (hf - ho, 1.0)
                fac_mats["interaction_F_minus_T_minus_B_plus_O"][si] += (hf - ht - hb + ho, 1.0)

            return {
                "label": label,
                "pair_count": len(subset_pairs),
                "hit_rates": {k: scene_cluster_ratio_ci(v, draws) for k, v in cond_hit.items()},
                "valid_rates": {k: scene_cluster_ratio_ci(v, draws) for k, v in cond_val.items()},
                "flips_vs_original": {k: scene_cluster_ratio_ci(v, draws) for k, v in flips_vs_o.items()},
                "gains_vs_original": {k: scene_cluster_ratio_ci(v, draws) for k, v in gains_vs_o.items()},
                "losses_vs_original": {k: scene_cluster_ratio_ci(v, draws) for k, v in losses_vs_o.items()},
                "displacement_px_vs_original": {k: scene_cluster_ratio_ci(v, draws) for k, v in disp_vs_o.items()},
                "factorial_effects": {k: scene_cluster_ratio_ci(v, draws) for k, v in fac_mats.items()},
                "full_minus_photometric_flip_rate": scene_cluster_diff_ci(flips_vs_o["F"], flips_vs_o["photo"], draws),
                "target_minus_background_flip_rate": scene_cluster_diff_ci(flips_vs_o["T"], flips_vs_o["B"], draws),
            }

        def _stratify_by_key(group_key: str) -> dict[str, Any]:
            groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
            for r in orig_pairs:
                groups[str(features_by_pair[r["pair_id"]][group_key])].append(r)
            out_g: dict[str, Any] = {}
            n_s = len(scene_pos)
            for gname, g_pairs in sorted(groups.items()):
                o_m = np.zeros((n_s, 2), dtype=np.float64)
                f_m = np.zeros((n_s, 2), dtype=np.float64)
                gain_m = np.zeros((n_s, 2), dtype=np.float64)
                loss_m = np.zeros((n_s, 2), dtype=np.float64)
                flip_m = np.zeros((n_s, 2), dtype=np.float64)
                net_m = np.zeros((n_s, 2), dtype=np.float64)
                for r in g_pairs:
                    pid = r["pair_id"]
                    si = scene_pos[r["scene_id"]]
                    a = idx_oc.get((pid, "original"))
                    b = idx_oc.get((pid, "converted"))
                    if a is None or b is None:
                        continue
                    ah, bh = int(bool(a["hit"])), int(bool(b["hit"]))
                    o_m[si] += (ah, 1.0)
                    f_m[si] += (bh, 1.0)
                    gain_m[si] += (int(ah == 0 and bh == 1), 1.0)
                    loss_m[si] += (int(ah == 1 and bh == 0), 1.0)
                    flip_m[si] += (int(ah != bh), 1.0)
                    net_m[si] += (bh - ah, 1.0)
                out_g[gname] = {
                    "pair_count": len(g_pairs),
                    "orig_hit_rate": scene_cluster_ratio_ci(o_m, draws),
                    "conv_hit_rate": scene_cluster_ratio_ci(f_m, draws),
                    "gain_rate": scene_cluster_ratio_ci(gain_m, draws),
                    "loss_rate": scene_cluster_ratio_ci(loss_m, draws),
                    "flip_rate": scene_cluster_ratio_ci(flip_m, draws),
                    "net_delta": scene_cluster_ratio_ci(net_m, draws),
                }
            return out_g

        return {
            "all_480_pairs": _subset_report(orig_pairs, "all_480_pairs"),
            "exact_473_identical_mask_pairs": _subset_report(exact_mask_pairs, "exact_mask_match"),
            "stratified_by_prior_optical_regime": _stratify_by_key("prior_optical_regime"),
            "stratified_by_pixel_optical_regime": _stratify_by_key("pixel_optical_regime"),
        }

    by_model = {mkey: _analyze_one_cf_model(oc_p, cf_p) for mkey, oc_p, cf_p in cf_candidates}
    primary_key = "qwen3_vl_8b" if "qwen3_vl_8b" in by_model else next(iter(by_model))
    primary = by_model[primary_key]
    cross_summary = {
        mk: {
            "flip_photo": rep["all_480_pairs"]["flips_vs_original"]["photo"],
            "flip_B": rep["all_480_pairs"]["flips_vs_original"]["B"],
            "flip_T": rep["all_480_pairs"]["flips_vs_original"]["T"],
            "flip_F": rep["all_480_pairs"]["flips_vs_original"]["F"],
            "full_minus_photometric_flip_rate": rep["all_480_pairs"]["full_minus_photometric_flip_rate"],
            "interaction_F_minus_T_minus_B_plus_O": rep["all_480_pairs"]["factorial_effects"]["interaction_F_minus_T_minus_B_plus_O"],
            "reflective_metallic_net_delta": rep["stratified_by_prior_optical_regime"].get("Reflective/Metallic", {}).get("net_delta"),
        }
        for mk, rep in by_model.items()
    }
    return {
        "primary_model_key": primary_key,
        "all_480_pairs": primary["all_480_pairs"],
        "exact_473_identical_mask_pairs": primary["exact_473_identical_mask_pairs"],
        "stratified_by_prior_optical_regime_8b": primary["stratified_by_prior_optical_regime"],
        "stratified_by_pixel_optical_regime_8b": primary["stratified_by_pixel_optical_regime"],
        "by_model": by_model,
        "cross_family_counterfactual_summary": cross_summary,
    }


def _evaluate_risk_scores(
    *,
    y_true: np.ndarray,
    scores: np.ndarray,
    scene_ids: list[str],
    draws_seed: int = 20261114,
    fractions: tuple[float, ...] = (0.1, 0.2, 0.3),
) -> dict[str, Any]:
    n = len(y_true)
    pos_total = int(y_true.sum())
    order = np.argsort(-scores, kind="mergesort")
    y_desc = y_true[order]

    sel_recall: dict[str, float | None] = {}
    hybrid_curve: list[dict[str, float]] = []
    for frac in fractions:
        k = max(1, int(round(frac * n)))
        rec = float(y_desc[:k].sum() / pos_total) if pos_total > 0 else None
        sel_recall[f"top_{int(round(frac * 100))}pct_recall"] = rec
        hybrid_curve.append(
            {
                "review_fraction": float(frac),
                "flagged_pairs": float(k),
                "losses_caught": float(y_desc[:k].sum()),
                "loss_recall": rec if rec is not None else 0.0,
            }
        )

    # Scene-cluster bootstrap on the evaluated split
    uniq_scenes = sorted(set(scene_ids))
    pos_map = {s: i for i, s in enumerate(uniq_scenes)}
    by_scene_idx: list[list[int]] = [[] for _ in uniq_scenes]
    for i, sid in enumerate(scene_ids):
        by_scene_idx[pos_map[sid]].append(i)
    rng = np.random.default_rng(draws_seed)
    aucs, auprcs, rec20s = [], [], []
    k_frac20 = 0.20
    for _ in range(2000):
        sampled_sc = rng.integers(0, len(uniq_scenes), size=len(uniq_scenes))
        idxs = np.array([ix for sc in sampled_sc for ix in by_scene_idx[sc]], dtype=np.int64)
        yb, sb = y_true[idxs], scores[idxs]
        a = roc_auc_score_np(yb, sb)
        ap = average_precision_np(yb, sb)
        if a is not None:
            aucs.append(a)
        if ap is not None:
            auprcs.append(ap)
        if yb.sum() > 0:
            kk = max(1, int(round(k_frac20 * len(yb))))
            rec20s.append(float(yb[np.argsort(-sb, kind="mergesort")][:kk].sum() / yb.sum()))

    return {
        "n": int(n),
        "positives": pos_total,
        "prevalence": float(pos_total / max(n, 1)),
        "auroc": roc_auc_score_np(y_true, scores),
        "auprc": average_precision_np(y_true, scores),
        "auroc_ci95": np.quantile(aucs, [0.025, 0.975]).tolist() if aucs else None,
        "auprc_ci95": np.quantile(auprcs, [0.025, 0.975]).tolist() if auprcs else None,
        "recall_at_20pct_ci95": np.quantile(rec20s, [0.025, 0.975]).tolist() if rec20s else None,
        **sel_recall,
        "selective_hybrid_curve": hybrid_curve,
    }


def analyze_risk_auditor(
    *,
    orig_pairs: list[dict[str, Any]],
    features_by_pair: dict[str, dict[str, Any]],
    v1_runs_dir: Path,
    v3_runs_dir: Path | None = None,
) -> dict[str, Any]:
    p8_path = v1_runs_dir / "8b" / "formal_repeat0" / "predictions.jsonl"
    p32_path = v1_runs_dir / "32b" / "formal_repeat0" / "predictions.jsonl"
    if not p8_path.is_file() or not p32_path.is_file():
        return {"status": "missing_formal_8b_32b_runs"}

    idx8 = _index_oc_predictions(_read_jsonl(p8_path))
    idx32 = _index_oc_predictions(_read_jsonl(p32_path))

    family_idxs: dict[str, dict[tuple[str, str], dict[str, Any]]] = {
        "qwen3_vl_8b": idx8,
        "qwen3_vl_32b": idx32,
    }
    if v3_runs_dir is not None and v3_runs_dir.is_dir():
        for folder in sorted(v3_runs_dir.glob("formal_*")):
            comp = folder / "completion.json"
            pred = folder / "predictions.jsonl"
            if not pred.is_file():
                continue
            if comp.is_file() and json.loads(comp.read_text(encoding="utf-8")).get("status") != "complete":
                continue
            mkey = folder.name.replace("formal_", "", 1)
            family_idxs[mkey] = _index_oc_predictions(_read_jsonl(pred))

    rows: list[dict[str, Any]] = []
    for r in orig_pairs:
        pid = r["pair_id"]
        feat = features_by_pair[pid]
        a8, b8 = idx8[(pid, "original")], idx8[(pid, "converted")]
        a32, b32 = idx32[(pid, "original")], idx32[(pid, "converted")]
        loss8 = int(bool(a8["hit"]) and not bool(b8["hit"]))
        loss32 = int(bool(a32["hit"]) and not bool(b32["hit"]))
        any_fam_loss = 0
        for fidx in family_idxs.values():
            fa, fb = fidx.get((pid, "original")), fidx.get((pid, "converted"))
            if fa is not None and fb is not None and bool(fa["hit"]) and not bool(fb["hit"]):
                any_fam_loss = 1
                break
        rows.append(
            {
                "pair_id": pid,
                "scene_id": feat["scene_id"],
                "split": feat["split"],
                "features": feat,
                "any_8b_32b_loss": int(bool(loss8 or loss32)),
                "any_family_loss": any_fam_loss,
                "8b_loss": loss8,
                "32b_loss": loss32,
                "8b_flip": int(bool(a8["hit"]) != bool(b8["hit"])),
            }
        )

    train_idx = [i for i, r in enumerate(rows) if r["split"] == "train"]
    val_idx = [i for i, r in enumerate(rows) if r["split"] == "validation"]
    test_idx = [i for i, r in enumerate(rows) if r["split"] == "test"]
    test_scenes = [rows[i]["scene_id"] for i in test_idx]
    all_scenes = [r["scene_id"] for r in rows]
    uniq_scenes = sorted(set(all_scenes))

    feature_sets: dict[str, tuple[str, ...]] = {
        "deploy_auto": DEPLOY_AUTO_FEATURES,
        "pixel_only": PIXEL_ONLY_FEATURES,
        "geometry_only": GEOM_FEATURES,
        "all_with_review_priors": FEATURE_NAMES_ALL,
    }

    targets = ("any_8b_32b_loss", "any_family_loss", "8b_loss", "32b_loss", "8b_flip")
    out_targets: dict[str, Any] = {}

    for tgt in targets:
        y_all = np.array([r[tgt] for r in rows], dtype=np.int64)
        model_reports: dict[str, Any] = {}

        for fs_name, feat_cols in feature_sets.items():
            X_all = np.array([[float(r["features"][c]) for c in feat_cols] for r in rows], dtype=np.float64)

            best_c = 1.0
            best_val_auc = -1.0
            for c_val in C_GRID:
                fit_m = fit_standardized_l2_logreg(X_all[train_idx], y_all[train_idx], c_reg=c_val)
                val_scores = predict_proba_logreg(fit_m, X_all[val_idx])
                auc = roc_auc_score_np(y_all[val_idx], val_scores) or 0.0
                if auc > best_val_auc:
                    best_val_auc = auc
                    best_c = c_val

            train_fit = fit_standardized_l2_logreg(X_all[train_idx], y_all[train_idx], c_reg=best_c)
            test_scores = predict_proba_logreg(train_fit, X_all[test_idx])
            test_eval = _evaluate_risk_scores(y_true=y_all[test_idx], scores=test_scores, scene_ids=test_scenes)

            # 30-fold Leave-One-Scene-Out CV at tuned C
            loso_scores = np.zeros(len(rows), dtype=np.float64)
            for sc in uniq_scenes:
                tr_i = [i for i, r in enumerate(rows) if r["scene_id"] != sc]
                te_i = [i for i, r in enumerate(rows) if r["scene_id"] == sc]
                fold_fit = fit_standardized_l2_logreg(X_all[tr_i], y_all[tr_i], c_reg=best_c)
                loso_scores[te_i] = predict_proba_logreg(fold_fit, X_all[te_i])
            loso_eval = _evaluate_risk_scores(y_true=y_all, scores=loso_scores, scene_ids=all_scenes)

            coefs = sorted(
                zip(feat_cols, [float(v) for v in train_fit["w"]]),
                key=lambda kv: abs(kv[1]),
                reverse=True,
            )
            model_reports[fs_name] = {
                "selected_c": best_c,
                "val_auroc_at_c": best_val_auc,
                "test_10_scenes": test_eval,
                "loso_30_scenes": loso_eval,
                "standardized_coefficients_train_fit": [{"feature": f, "coef": w} for f, w in coefs],
            }

        # Scalar baselines (no fitting on train)
        for scalar_feat in ("global_rgb_mae", "target_rgb_mae"):
            s_all = np.array([float(r["features"][scalar_feat]) for r in rows], dtype=np.float64)
            model_reports[f"baseline_{scalar_feat}"] = {
                "test_10_scenes": _evaluate_risk_scores(y_true=y_all[test_idx], scores=s_all[test_idx], scene_ids=test_scenes),
                "loso_30_scenes": _evaluate_risk_scores(y_true=y_all, scores=s_all, scene_ids=all_scenes),
            }

        prev_test = float(y_all[test_idx].mean())
        prev_all = float(y_all.mean())
        model_reports["baseline_random"] = {
            "test_10_scenes": {"prevalence": prev_test, "auroc": 0.5, "auprc": prev_test, "top_10pct_recall": 0.1, "top_20pct_recall": 0.2, "top_30pct_recall": 0.3},
            "loso_30_scenes": {"prevalence": prev_all, "auroc": 0.5, "auprc": prev_all, "top_10pct_recall": 0.1, "top_20pct_recall": 0.2, "top_30pct_recall": 0.3},
        }
        out_targets[tgt] = model_reports

    return {
        "split_sizes": {"train": len(train_idx), "validation": len(val_idx), "test": len(test_idx)},
        "models_included_in_any_family": sorted(family_idxs),
        "targets": out_targets,
    }


def run_all_analyses(
    *,
    manifest_path: Path,
    scenes_path: Path,
    protocol_path: Path,
    render_controls_path: Path,
    features_path: Path,
    v1_runs_dir: Path,
    v3_runs_dir: Path,
    out_dir: Path,
) -> dict[str, Any]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    orig_pairs = [r for r in manifest["records"] if r["condition"] == "original"]
    scenes_raw = json.loads(scenes_path.read_text(encoding="utf-8"))
    scene_ids = sorted(r["scene_id"] for r in scenes_raw["scenes"])
    scene_pos = {s: i for i, s in enumerate(scene_ids)}
    draws = np.random.default_rng(20261114).integers(0, len(scene_ids), size=(10000, len(scene_ids)))

    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    ctrl_scenes = list(protocol["render_noise_control_scene_ids"])

    feats_raw = json.loads(features_path.read_text(encoding="utf-8"))
    features_by_pair = {r["pair_id"]: r for r in feats_raw["records"]}

    out_dir.mkdir(parents=True, exist_ok=True)

    scaling = analyze_scaling_and_families(
        orig_pairs=orig_pairs,
        scene_pos=scene_pos,
        draws=draws,
        v1_runs_dir=v1_runs_dir,
        v3_runs_dir=v3_runs_dir,
    )
    (out_dir / "scaling_and_families.json").write_text(json.dumps(scaling, indent=2) + "\n", encoding="utf-8")

    variance = analyze_variance_decomposition(
        orig_pairs=orig_pairs,
        control_scene_ids=ctrl_scenes,
        v1_runs_dir=v1_runs_dir,
        render_controls_path=render_controls_path,
        v3_runs_dir=v3_runs_dir,
    )
    (out_dir / "variance_decomposition.json").write_text(json.dumps(variance, indent=2) + "\n", encoding="utf-8")

    mechanisms = analyze_optical_mechanisms(
        orig_pairs=orig_pairs,
        scene_pos=scene_pos,
        draws=draws,
        features_by_pair=features_by_pair,
        v1_runs_dir=v1_runs_dir,
        v3_runs_dir=v3_runs_dir,
    )
    (out_dir / "optical_mechanisms.json").write_text(json.dumps(mechanisms, indent=2) + "\n", encoding="utf-8")

    risk = analyze_risk_auditor(
        orig_pairs=orig_pairs,
        features_by_pair=features_by_pair,
        v1_runs_dir=v1_runs_dir,
        v3_runs_dir=v3_runs_dir,
    )
    (out_dir / "risk_auditor.json").write_text(json.dumps(risk, indent=2) + "\n", encoding="utf-8")

    return {
        "scaling_models": sorted(scaling["models"]),
        "variance_keys": sorted(variance),
        "mechanisms_ready": "all_480_pairs" in mechanisms,
        "risk_ready": "targets" in risk,
    }


def main() -> int:
    root = repo_root_from_script(Path(__file__))
    raw_v1 = root / "paper/shared/evidence/raw/cviu_formal/v1"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=raw_v1 / "manifest.json")
    parser.add_argument("--scenes", type=Path, default=raw_v1 / "scenes.json")
    parser.add_argument("--protocol", type=Path, default=raw_v1 / "protocol.json")
    parser.add_argument("--render-controls", type=Path, default=raw_v1 / "analysis_v1/render_controls.json")
    parser.add_argument("--features", type=Path, default=root / "paper/shared/evidence/raw/cviu_v3/pair_optical_features.json")
    parser.add_argument("--v1-runs-dir", type=Path, default=Path("/cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/formal_model_runs_v1"))
    parser.add_argument("--v3-runs-dir", type=Path, default=Path("/tmp/cviu_v3_work/runs"))
    parser.add_argument("--out-dir", type=Path, default=root / "paper/shared/evidence/raw/cviu_v3")
    args = parser.parse_args()

    summary = run_all_analyses(
        manifest_path=args.manifest.resolve(),
        scenes_path=args.scenes.resolve(),
        protocol_path=args.protocol.resolve(),
        render_controls_path=args.render_controls.resolve(),
        features_path=args.features.resolve(),
        v1_runs_dir=args.v1_runs_dir.resolve(),
        v3_runs_dir=args.v3_runs_dir.resolve(),
        out_dir=args.out_dir.resolve(),
    )
    print("[ok] analyze_v3_all:", json.dumps(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
