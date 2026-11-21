#!/usr/bin/env python3
"""Unit tests for the CVIU v3 counterfactual, optical feature, and risk-gate pipeline."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parents[1]
EXP_V3_DIR = REPO_ROOT / "paper" / "shared" / "evidence" / "experiments" / "14_cviu_v3"
sys.path.insert(0, str(EXP_V3_DIR))

import analyze_v3_all  # noqa: E402
import build_counterfactual_inputs  # noqa: E402
import optical_and_risk_features  # noqa: E402
import run_v3_vlm_suite  # noqa: E402
import v3_common  # noqa: E402


class TestCVIUV3Pipeline(unittest.TestCase):
    def test_lab_roundtrip_and_photometric_match(self) -> None:
        rng = np.random.default_rng(42)
        src = rng.integers(20, 235, size=(64, 64, 3), dtype=np.uint8)
        lab, _ = v3_common.srgb_uint8_to_lab(src)
        rec = v3_common.lab_to_srgb_uint8(lab)
        max_diff = int(np.max(np.abs(src.astype(np.int16) - rec.astype(np.int16))))
        self.assertLessEqual(max_diff, 1)

        mask = np.zeros((64, 64), dtype=bool)
        mask[16:48, 16:48] = True
        # Darken background, brighten target in reference image
        ref = src.copy().astype(np.float64)
        ref[mask] = np.clip(ref[mask] * 1.15 + 15.0, 0, 255)
        ref[~mask] = np.clip(ref[~mask] * 0.65 - 10.0, 0, 255)
        ref_u8 = ref.astype(np.uint8)

        matched = build_counterfactual_inputs.affine_lab_match(src, ref_u8, mask)
        m_lab, _ = v3_common.srgb_uint8_to_lab(matched)
        r_lab, _ = v3_common.srgb_uint8_to_lab(ref_u8)
        for region in (mask, ~mask):
            self.assertLess(abs(float(m_lab[region, 0].mean() - r_lab[region, 0].mean())), 2.0)

    def test_silhouette_mask_composites_with_support_change(self) -> None:
        orig = np.full((32, 32, 3), 50, dtype=np.uint8)
        conv = np.full((32, 32, 3), 200, dtype=np.uint8)
        orig_mask = np.zeros((32, 32), dtype=bool)
        orig_mask[8:16, 8:16] = True
        conv_mask = np.zeros((32, 32), dtype=bool)
        conv_mask[8:20, 8:20] = True

        arrs = build_counterfactual_inputs.synthesize_counterfactual_arrays(orig, conv, orig_mask, conv_mask)
        # target_only: converted inside conv_mask, original outside
        self.assertTrue(np.all(arrs["target_only"][conv_mask] == 200))
        self.assertTrue(np.all(arrs["target_only"][~conv_mask] == 50))
        # background_only: original inside orig_mask, converted outside
        self.assertTrue(np.all(arrs["background_only"][orig_mask] == 50))
        self.assertTrue(np.all(arrs["background_only"][~orig_mask] == 200))

    def test_optical_features_detect_glare_texture_and_contrast_drop(self) -> None:
        h, w = 96, 128
        orig = np.full((h, w, 3), 40, dtype=np.uint8)
        mask = np.zeros((h, w), dtype=bool)
        mask[24:72, 32:96] = True

        # Textured + specular original target with bright border
        yy, xx = np.indices((h, w))
        checker = (((yy // 2) + (xx // 2)) % 2) * 80 + 90
        orig[mask, 0] = checker[mask]
        orig[mask, 1] = checker[mask]
        orig[mask, 2] = checker[mask]
        orig[30:38, 40:50, :] = 252  # specular highlight patch inside target

        # Flattened low-contrast, highlight-stripped converted target
        conv = orig.copy()
        conv[mask] = 75

        identical = optical_and_risk_features.compute_pair_optical_features(
            orig_rgb=orig,
            conv_rgb=orig,
            orig_mask=mask,
            conv_mask=mask,
            source_category="bowl",
            query="Point to the bowl.",
        )
        self.assertAlmostEqual(identical["target_ssim"], 1.0, places=5)
        self.assertAlmostEqual(identical["global_rgb_mae"], 0.0, places=6)

        feats = optical_and_risk_features.compute_pair_optical_features(
            orig_rgb=orig,
            conv_rgb=conv,
            orig_mask=mask,
            conv_mask=mask,
            source_category="faucet",
            query="Point to the chrome faucet.",
            visual_evidence="Metallic reflections reduced cleanly.",
        )
        self.assertLess(feats["target_specular_delta"], -0.02)
        self.assertLess(feats["target_sobel_edge_ratio"], 0.3)
        self.assertLess(feats["boundary_contrast_delta"], 0.0)
        self.assertEqual(feats["is_reflective_appliance_or_metal"], 1)
        self.assertEqual(feats["pixel_optical_regime"], "Specular-Stripped")

    def test_parsers_and_scoring_geometry(self) -> None:
        mask = np.zeros((768, 1024), dtype=bool)
        mask[384:460, 512:620] = True
        self.assertEqual(v3_common.parse_point_by_mode("Point: 550, 520", "strict"), [550.0, 520.0])
        self.assertIsNone(v3_common.parse_point_by_mode("(550, 520)", "strict"))
        self.assertEqual(v3_common.parse_point_by_mode("Point: (550, 520)", "relaxed_xy"), [550.0, 520.0])
        self.assertEqual(
            v3_common.parse_point_by_mode('<point x="55.0" y="52.0" alt="obj">obj</point>', "molmo_0_100"),
            [550.0, 520.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode('<points coords="1 512 384"/>', "molmo2_1000"),
            [512.0, 384.0],
        )
        res = run_v3_vlm_suite.evaluate_raw_response("Point: 550, 520", mask, "strict")
        self.assertTrue(res["valid_point"] and res["hit"] and res["visible_bbox_hit"])

    def test_end_to_end_analysis_factorial_bootstrap_and_risk_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            troot = Path(tmp)
            assets = troot / "assets"
            v1_runs = assets / "formal_model_runs_v1"
            v3_runs = troot / "v3_runs"
            out_dir = troot / "out"
            reviews_dir = troot / "reviews"
            reviews_dir.mkdir(parents=True)

            # Build synthetic 30-scene cohort (15 train, 5 val, 10 test; 2 pairs/scene = 60 pairs for fast unit test)
            scenes = []
            for s_idx in range(30):
                split = "train" if s_idx < 15 else ("validation" if s_idx < 20 else "test")
                scenes.append({"scene_id": f"scene_{s_idx:02d}", "family": "home_scenes", "split": split})
            scenes_path = troot / "scenes.json"
            scenes_path.write_text(json.dumps({"scenes": scenes}), encoding="utf-8")

            protocol_path = troot / "protocol.json"
            ctrl_scenes = ["scene_00", "scene_01", "scene_02"]
            protocol_path.write_text(
                json.dumps({"render_noise_control_scene_ids": ctrl_scenes}),
                encoding="utf-8",
            )

            img_dir = troot / "imgs"
            img_dir.mkdir()
            mask_hit = np.zeros((64, 64), dtype=bool)
            mask_hit[16:48, 16:48] = True
            mask_p = img_dir / "mask.npy"
            np.save(mask_p, mask_hit)
            mask_sha = hashlib.sha256(mask_p.read_bytes()).hexdigest()

            manifest_records = []
            feat_records = []
            p8_rows = []
            p32_rows = []
            cf_rows = []
            stoch_rows = []

            rng = np.random.default_rng(123)
            for s_idx, sc in enumerate(scenes):
                sid = sc["scene_id"]
                for obj_i in range(2):
                    pid = f"{sid}:obj{obj_i}:v0"
                    # Construct clean contrast signal for Risk Auditor: 20% positives -> top 30% catches 100%
                    is_loss = (s_idx + obj_i) % 5 == 0
                    high_mae = 0.48 + 0.02 * rng.random() if is_loss else 0.08 + 0.02 * rng.random()
                    o_img = np.full((64, 64, 3), 120, dtype=np.uint8)
                    c_img = np.full((64, 64, 3), 245 if is_loss else 140, dtype=np.uint8)
                    op = img_dir / f"{sid}_{obj_i}_o.png"
                    cp = img_dir / f"{sid}_{obj_i}_c.png"
                    Image.fromarray(o_img).save(op)
                    Image.fromarray(c_img).save(cp)

                    for cond, ip in (("original", op), ("converted", cp)):
                        manifest_records.append(
                            {
                                "pair_id": pid,
                                "condition": cond,
                                "scene_id": sid,
                                "target_prim": f"/World/obj{obj_i}",
                                "view_id": "v0",
                                "query": f"Point to the obj{obj_i}.",
                                "source_category": "bottle" if is_loss else "chair",
                                "image": {"path": str(ip), "sha256": v3_common.sha256_file(ip), "width": 64, "height": 64},
                                "mask": {"path": str(mask_p), "sha256": mask_sha, "pixels": int(mask_hit.sum())},
                            }
                        )

                    feat_records.append(
                        {
                            "pair_id": pid,
                            "scene_id": sid,
                            "split": sc["split"],
                            "family": "home_scenes",
                            "target_prim": f"/World/obj{obj_i}",
                            "view_id": "v0",
                            "query": f"Point to the obj{obj_i}.",
                            "source_category": "bottle" if is_loss else "chair",
                            "prior_optical_regime": "Transparent/Glass" if is_loss else "Matte/Diffuse",
                            "pixel_optical_regime": "Texture/Detail-Degraded" if is_loss else "Low-Distortion",
                            **{k: 0.0 for k in optical_and_risk_features.FEATURE_NAMES_ALL},
                            "mask_iou": 1.0,
                            "target_rgb_mae": high_mae,
                            "global_rgb_mae": high_mae * 0.25,
                            "target_ssim": 0.2 if is_loss else 0.9,
                            "boundary_contrast_delta": -20.0 if is_loss else 1.0,
                            "target_sobel_edge_ratio": 0.4 if is_loss else 0.98,
                        }
                    )

                    # Predictions: O hits, F misses when is_loss else hits; T=F, B=O, photo=O
                    hit_f = not is_loss
                    for cond, hit in (("original", True), ("converted", hit_f)):
                        pt = [500.0, 500.0] if hit else [50.0, 50.0]
                        base = {"pair_id": pid, "condition": cond, "scene_id": sid, "status": "ok", "valid_point": True, "point_normalized": pt, "hit": hit}
                        p8_rows.append(base)
                        p32_rows.append({**base, "hit": True if (not is_loss or obj_i == 0) else False, "point_normalized": [500.0, 500.0] if (not is_loss or obj_i == 0) else [50.0, 50.0]})
                        if sid in ctrl_scenes:
                            for d_i in range(3):
                                d_hit = hit if d_i != 1 else (not hit if obj_i == 0 else hit)
                                stoch_rows.append({**base, "draw_idx": d_i, "raw_response": f"d{d_i}", "hit": d_hit})

                    for cf_cond, hit in (("target_only", hit_f), ("background_only", True), ("photometric_matched", True)):
                        cf_rows.append(
                            {
                                "pair_id": pid,
                                "condition": cf_cond,
                                "scene_id": sid,
                                "status": "ok",
                                "valid_point": True,
                                "point_normalized": [500.0, 500.0] if hit else [50.0, 50.0],
                                "hit": hit,
                            }
                        )

            manifest_path = troot / "manifest.json"
            manifest_path.write_text(json.dumps({"records": manifest_records}), encoding="utf-8")
            features_path = troot / "pair_optical_features.json"
            features_path.write_text(json.dumps({"records": feat_records}), encoding="utf-8")
            rc_path = troot / "render_controls.json"
            rc_path.write_text(
                json.dumps(
                    {
                        "models": {
                            "8b": {"same_condition_render_repeat_all": {"n": 12, "hit_flip": 1, "mean_point_displacement_px": 4.0}},
                            "32b": {"same_condition_render_repeat_all": {"n": 12, "hit_flip": 0, "mean_point_displacement_px": 2.0}},
                        }
                    }
                ),
                encoding="utf-8",
            )

            for m_short, rows in (("8b", p8_rows), ("32b", p32_rows)):
                for rep in range(3):
                    rdir = v1_runs / m_short / f"formal_repeat{rep}"
                    rdir.mkdir(parents=True, exist_ok=True)
                    (rdir / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in rows) + "\n", encoding="utf-8")

            st_dir = v3_runs / "stochastic_control_qwen3_vl_8b"
            st_dir.mkdir(parents=True, exist_ok=True)
            (st_dir / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in stoch_rows) + "\n", encoding="utf-8")
            cf_dir = v3_runs / "counterfactual_qwen3_vl_8b"
            cf_dir.mkdir(parents=True, exist_ok=True)
            (cf_dir / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in cf_rows) + "\n", encoding="utf-8")

            # Add synthetic InternVL3.5-8B formal + control_repeat + control_rerender + counterfactual
            iv_formal = v3_runs / "formal_internvl3_5_8b"
            iv_formal.mkdir(parents=True, exist_ok=True)
            (iv_formal / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in p8_rows) + "\n", encoding="utf-8")
            (iv_formal / "completion.json").write_text(json.dumps({"status": "complete"}) + "\n", encoding="utf-8")
            (iv_formal / "metadata.json").write_text(json.dumps({"model_key": "internvl3_5_8b", "hf_repo": "OpenGVLab/InternVL3_5-8B-HF", "family": "InternVL3.5"}) + "\n", encoding="utf-8")

            ctrl_rows = [x for x in p8_rows if x["scene_id"] in ctrl_scenes]
            iv_cr = v3_runs / "control_repeat_internvl3_5_8b"
            iv_cr.mkdir(parents=True, exist_ok=True)
            (iv_cr / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in ctrl_rows) + "\n", encoding="utf-8")

            iv_rr = v3_runs / "control_rerender_internvl3_5_8b"
            iv_rr.mkdir(parents=True, exist_ok=True)
            rr_rows = [{**x, "hit": (not x["hit"]) if i == 0 else x["hit"]} for i, x in enumerate(ctrl_rows)]
            (iv_rr / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in rr_rows) + "\n", encoding="utf-8")

            iv_cf = v3_runs / "counterfactual_internvl3_5_8b"
            iv_cf.mkdir(parents=True, exist_ok=True)
            (iv_cf / "predictions.jsonl").write_text("\n".join(json.dumps(x) for x in cf_rows) + "\n", encoding="utf-8")
            (iv_cf / "completion.json").write_text(json.dumps({"status": "complete"}) + "\n", encoding="utf-8")

            summary = analyze_v3_all.run_all_analyses(
                manifest_path=manifest_path,
                scenes_path=scenes_path,
                protocol_path=protocol_path,
                render_controls_path=rc_path,
                features_path=features_path,
                v1_runs_dir=v1_runs,
                v3_runs_dir=v3_runs,
                out_dir=out_dir,
            )
            self.assertTrue(summary["mechanisms_ready"])
            self.assertTrue(summary["risk_ready"])

            vd = json.loads((out_dir / "variance_decomposition.json").read_text(encoding="utf-8"))
            self.assertEqual(vd["level1_greedy_process_repeat"]["internvl3_5_8b"]["pairwise_hit_disagreement_rate"], 0.0)
            self.assertGreater(vd["level3_raytracing_rerender"]["internvl3_5_8b"]["hit_flip_rate"], 0.0)
            self.assertIn("internvl3_5_8b", vd["level4_material_conversion_on_control_pairs"])

            mech = json.loads((out_dir / "optical_mechanisms.json").read_text(encoding="utf-8"))
            self.assertIn("qwen3_vl_8b", mech["by_model"])
            self.assertIn("internvl3_5_8b", mech["by_model"])
            fac = mech["all_480_pairs"]["factorial_effects"]
            # Since F == T and B == O, F - T - B + O must equal 0 exactly
            self.assertAlmostEqual(fac["interaction_F_minus_T_minus_B_plus_O"]["estimate"], 0.0, places=9)
            self.assertAlmostEqual(fac["T_minus_O"]["estimate"], -0.2, places=6)
            self.assertEqual(mech["all_480_pairs"]["flips_vs_original"]["photo"]["estimate"], 0.0)

            risk = json.loads((out_dir / "risk_auditor.json").read_text(encoding="utf-8"))
            auroc_test = risk["targets"]["any_8b_32b_loss"]["deploy_auto"]["test_10_scenes"]["auroc"]
            auroc_loso = risk["targets"]["any_8b_32b_loss"]["deploy_auto"]["loso_30_scenes"]["auroc"]
            self.assertGreater(auroc_test, 0.90)
            self.assertGreater(auroc_loso, 0.90)
            self.assertIn("any_family_loss", risk["targets"])
            self.assertGreater(risk["targets"]["any_family_loss"]["deploy_auto"]["test_10_scenes"]["auroc"], 0.90)
            self.assertAlmostEqual(risk["targets"]["any_8b_32b_loss"]["deploy_auto"]["test_10_scenes"]["top_30pct_recall"], 1.0, places=5)

    def test_molmo2_and_parser_modes(self) -> None:
        self.assertEqual(
            v3_common.parse_point_by_mode('<points coords="1 1 502 598">stool</points>', "molmo2_1000"),
            [502.0, 598.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode('<points coords="1 1 45 320">lamp</points>', "molmo2_1000"),
            [45.0, 320.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode('<points coords="1 512 430"/>', "molmo2_1000"),
            [512.0, 430.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("Point: 512, 430", "molmo2_1000"),
            [512.0, 430.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("<Point: 500 700>", "molmo2_1000"),
            [500.0, 700.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("<Point: 680 500 2 777 500>", "molmo2_1000"),
            [680.0, 500.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("Point: 0.333,0.133,0.633,0.988 ", "unit_float_xy"),
            [483.0, 560.5],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("Point: 0.333,0.400 ", "unit_float_xy"),
            [333.0, 400.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("Point: 512, 430", "unit_float_xy"),
            [512.0, 430.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("(400, 375, 915, 895)", "flex_1000"),
            [657.5, 635.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("Point: 155, 220, 594, 734", "flex_1000"),
            [374.5, 477.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode("(144, 185)", "flex_1000"),
            [144.0, 185.0],
        )
        self.assertEqual(
            v3_common.parse_point_by_mode('```json\n[{"point_2d": [700, 451], "label": "armchair"}]\n```', "flex_1000"),
            [700.0, 451.0],
        )


if __name__ == "__main__":
    unittest.main()
