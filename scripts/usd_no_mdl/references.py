# -*- coding: utf-8 -*-
from pxr import Usd, Sdf
import os
from .config import RESTORE_VARIANT_SELECTION
from .path_utils import _resolve, _relpath


def _listop_items(listop):
    if not listop:
        return []
    items = []
    for name in ("GetExplicitItems", "GetAddedItems", "GetPrependedItems", "GetAppendedItems"):
        if hasattr(listop, name):
            items.extend(getattr(listop, name)())
    return items


def _collect_asset_paths(stage: Usd.Stage):
    items = []
    layer = stage.GetRootLayer()
    ldir = os.path.dirname(layer.realPath or layer.identifier)

    for sl in layer.subLayerPaths:
        if sl:
            items.append(("sublayer", ("rootLayer", None), ldir, sl, None, None))

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if not prim.IsValid():
            continue
        # Read ListOp from metadata for USD versions without GetReferences()
        ref_lo = prim.GetMetadata("references")
        for r in _listop_items(ref_lo):
            items.append(("reference", ("prim", str(prim.GetPath())), ldir, r.assetPath, prim.GetPath(), r))
        pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
        for p in _listop_items(pay_lo):
            items.append(("payload", ("prim", str(prim.GetPath())), ldir, p.assetPath, prim.GetPath(), p))
        try:
            if prim.HasAuthoredMetadata("clips"):
                clips = prim.GetMetadata("clips")
                if isinstance(clips, dict):
                    cap = clips.get("clipAssetPaths")
                    if isinstance(cap, list):
                        for ap in cap:
                            items.append(("clip_asset", ("prim", str(prim.GetPath())), ldir, ap, prim.GetPath(), "clipAssetPaths"))
                    man = clips.get("manifestAssetPath")
                    if man:
                        items.append(("clip_manifest", ("prim", str(prim.GetPath())), ldir, man, prim.GetPath(), "manifestAssetPath"))
        except Exception:
            pass

        vsets = prim.GetVariantSets()
        for vs_name in vsets.GetNames():
            vs = vsets.GetVariantSet(vs_name)
            orig_sel = vs.GetVariantSelection()
            for vname in vs.GetVariantNames():
                with vs.GetVariantEditContext(vname):
                    ref_lo2 = prim.GetMetadata("references")
                    for r in _listop_items(ref_lo2):
                        items.append(("variant_ref", (str(prim.GetPath()), vs_name, vname), ldir, r.assetPath, prim.GetPath(), r))
                    pay_lo2 = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
                    for p in _listop_items(pay_lo2):
                        items.append(("variant_payload", (str(prim.GetPath()), vs_name, vname), ldir, p.assetPath, prim.GetPath(), p))
            if RESTORE_VARIANT_SELECTION and orig_sel:
                vs.SetVariantSelection(orig_sel)

    return items


def _rewrite_assets_in_stage(stage: Usd.Stage, mapping_src2dst: dict):
    layer = stage.GetRootLayer()
    ldir = os.path.dirname(layer.realPath or layer.identifier)

    changed = False
    new_subs = []
    for sl in layer.subLayerPaths:
        abs_sl = _resolve(ldir, sl)
        if abs_sl and abs_sl in mapping_src2dst:
            new_rel = _relpath(ldir, mapping_src2dst[abs_sl])
            new_subs.append(new_rel)
            changed = True
        else:
            new_subs.append(sl)
    if changed:
        layer.subLayerPaths = new_subs

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if not prim.IsValid():
            continue

        # references
        ref_api = prim.GetReferences()
        ref_lo = prim.GetMetadata("references")
        items_lo = _listop_items(ref_lo)
        if items_lo:
            new_items = []
            updated = False
            for it in items_lo:
                ap = _resolve(ldir, it.assetPath)
                if ap and ap in mapping_src2dst:
                    it = Sdf.Reference(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                    updated = True
                new_items.append(it)
            if updated:
                try:
                    ref_api.ClearReferences()
                    for it in new_items:
                        ref_api.AddReference(it)
                except Exception:
                    # Fallback: write back metadata
                    prim.SetMetadata("references", new_items)

        # payloads
        pay_api = prim.GetPayloads()
        pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
        items_lo = _listop_items(pay_lo)
        if items_lo:
            new_items = []
            updated = False
            for it in items_lo:
                ap = _resolve(ldir, it.assetPath)
                if ap and ap in mapping_src2dst:
                    it = Sdf.Payload(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                    updated = True
                new_items.append(it)
            if updated:
                try:
                    pay_api.ClearPayloads()
                    for it in new_items:
                        pay_api.AddPayload(it)
                except Exception:
                    prim.SetMetadata("payloads", new_items)

        try:
            if prim.HasAuthoredMetadata("clips"):
                clips = prim.GetMetadata("clips")
                if isinstance(clips, dict):
                    changed = False
                    cap = clips.get("clipAssetPaths", None)
                    if cap and isinstance(cap, list):
                        new_cap = []
                        for ap in cap:
                            abs_ap = _resolve(ldir, ap)
                            if abs_ap and abs_ap in mapping_src2dst:
                                new_cap.append(_relpath(ldir, mapping_src2dst[abs_ap]))
                                changed = True
                            else:
                                new_cap.append(ap)
                        clips["clipAssetPaths"] = new_cap
                    man = clips.get("manifestAssetPath", None)
                    if man:
                        abs_man = _resolve(ldir, man)
                        if abs_man and abs_man in mapping_src2dst:
                            clips["manifestAssetPath"] = _relpath(ldir, mapping_src2dst[abs_man])
                            changed = True
                    if changed:
                        prim.SetMetadata("clips", clips)
        except Exception:
            pass

        vsets = prim.GetVariantSets()
        for vs_name in vsets.GetNames():
            vs = vsets.GetVariantSet(vs_name)
            orig_sel = vs.GetVariantSelection()
            for vname in vs.GetVariantNames():
                with vs.GetVariantEditContext(vname):
                    ref_api = prim.GetReferences()
                    ref_lo = prim.GetMetadata("references")
                    items_lo = _listop_items(ref_lo)
                    if items_lo:
                        new_items = []
                        updated = False
                        for it in items_lo:
                            ap = _resolve(ldir, it.assetPath)
                            if ap and ap in mapping_src2dst:
                                it = Sdf.Reference(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                                updated = True
                            new_items.append(it)
                        if updated:
                            try:
                                ref_api.ClearReferences()
                                for it in new_items:
                                    ref_api.AddReference(it)
                            except Exception:
                                prim.SetMetadata("references", new_items)

                    pay_api = prim.GetPayloads()
                    pay_lo = prim.GetMetadata("payloads") or prim.GetMetadata("payload")
                    items_lo = _listop_items(pay_lo)
                    if items_lo:
                        new_items = []
                        updated = False
                        for it in items_lo:
                            ap = _resolve(ldir, it.assetPath)
                            if ap and ap in mapping_src2dst:
                                it = Sdf.Payload(_relpath(ldir, mapping_src2dst[ap]), it.primPath, it.layerOffset)
                                updated = True
                            new_items.append(it)
                        if updated:
                            try:
                                pay_api.ClearPayloads()
                                for it in new_items:
                                    pay_api.AddPayload(it)
                            except Exception:
                                prim.SetMetadata("payloads", new_items)
            if RESTORE_VARIANT_SELECTION and orig_sel:
                vs.SetVariantSelection(orig_sel)
