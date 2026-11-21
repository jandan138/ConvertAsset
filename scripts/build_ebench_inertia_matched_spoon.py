#!/usr/bin/env python3
"""Match authored inertial properties while preserving a target spoon geometry."""

import argparse
import hashlib
import json
from pathlib import Path

PROPERTIES = ("physics:mass", "physics:centerOfMass", "physics:diagonalInertia",
              "physics:principalAxes")


def build(reference, target, output, prim_path="/root/obj_spoon", *, properties=None):
    from pxr import Sdf, Usd

    chosen = tuple(PROPERTIES if properties is None else properties)
    if not chosen or len(chosen) != len(set(chosen)) or not set(chosen) <= set(PROPERTIES):
        raise ValueError("Choose unique supported inertial properties")
    if output.exists():
        raise FileExistsError(output)
    reference_stage = Usd.Stage.Open(str(reference))
    target_stage = Usd.Stage.Open(str(target))
    ref = reference_stage.GetPrimAtPath(prim_path)
    prim = target_stage.GetPrimAtPath(prim_path)
    if not ref or not prim:
        raise ValueError("Missing source spoon")
    for name in chosen:
        if not ref.GetAttribute(name).HasAuthoredValueOpinion():
            raise ValueError(f"Reference must explicitly author {name}")
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Usd.Stage.CreateNew(str(output))
    stage.GetRootLayer().subLayerPaths = [str(target.resolve())]
    stage.SetDefaultPrim(stage.GetPrimAtPath(target_stage.GetDefaultPrim().GetPath()))
    Sdf.CreatePrimInLayer(stage.GetRootLayer(), prim_path)
    flat = reference_stage.Flatten()
    for name in chosen:
        path = Sdf.Path(prim_path).AppendProperty(name)
        Sdf.CopySpec(flat, path, stage.GetRootLayer(), path)
    stage.GetRootLayer().Save()
    # Check composed values, including mesh points, UVs, materials and transforms.
    # The target is a retained native overlay, with no time-varying attributes.
    differences = []
    for old in target_stage.Traverse():
        new = stage.GetPrimAtPath(old.GetPath())
        if not new or old.GetAppliedSchemas() != new.GetAppliedSchemas():
            raise ValueError("Prim structure or API schemas changed")
        for attr in old.GetAttributes():
            updated = new.GetAttribute(attr.GetName())
            if attr.GetTimeSamples() or updated.GetTimeSamples():
                raise ValueError("Animated source is outside this diagnostic contract")
            if attr.Get() != updated.Get():
                differences.append(str(attr.GetPath()))
                if str(old.GetPath()) != prim_path or attr.GetName() not in chosen:
                    raise ValueError(f"Unexpected attribute change: {attr.GetPath()}")
            if attr.GetConnections() != updated.GetConnections():
                raise ValueError("Shader connection changed")
        for rel in old.GetRelationships():
            if rel.GetTargets() != new.GetRelationship(rel.GetName()).GetTargets():
                raise ValueError("Relationship changed")
    for name in chosen:
        if stage.GetPrimAtPath(prim_path).GetAttribute(name).Get() != ref.GetAttribute(name).Get():
            raise ValueError("Reference inertial property was not composed")
    report = {"schema": "convertasset.ebench.inertia_matched_spoon.v1",
              "reference": str(reference.resolve()), "target": str(target.resolve()),
              "output": str(output.resolve()), "changed_attributes": differences,
              "matched_properties": list(chosen), "static_validation": "passed",
              "implementation_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "runtime_readback": "pending", "physics_qualified": False,
              "source_bound_overlay": True,
              "sha256": {key: hashlib.sha256(path.read_bytes()).hexdigest()
                         for key, path in (("reference", reference), ("target", target), ("output", output))}}
    output.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--target", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--property", action="append", choices=PROPERTIES, dest="properties")
    args = parser.parse_args()
    print(json.dumps(build(args.reference, args.target, args.output, properties=args.properties), indent=2))


if __name__ == "__main__":
    main()
