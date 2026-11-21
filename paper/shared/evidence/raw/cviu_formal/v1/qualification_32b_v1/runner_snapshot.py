"""Local BF16 Qwen3-VL capacity comparison with strict formal input validation.

Qualification mode uses held-out pilot inputs only and never counts toward the
5,760 formal predictions. Model loading is GPU-only; no quantization or offload.
"""
import argparse
import hashlib
import importlib.util
import json
import random
import re
import shutil
import time
from collections import defaultdict
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def validate_structure(manifest, expected_scenes):
    if manifest.get('status') != 'frozen_formal_inputs':
        raise ValueError('Manifest has not passed formal freezing')
    rows = manifest['records']
    if len(rows) != 960:
        raise ValueError('Expected 960 condition-specific inputs')
    pairs = defaultdict(list)
    targets = defaultdict(lambda: defaultdict(set))
    keys = set()
    for row in rows:
        key = (row['pair_id'], row['condition'])
        if key in keys:
            raise ValueError('Duplicate condition-specific input')
        keys.add(key)
        pairs[row['pair_id']].append(row)
        targets[row['scene_id']][row['target_prim']].add(row['view_id'])
        if row.get('technical_qa') != 'PASS' or row.get('original_qualification') != 'PASS':
            raise ValueError('Unqualified paired input')
        if not row['query'].strip():
            raise ValueError('Missing query')
    if set(targets) != set(expected_scenes) or len(targets) != 30:
        raise ValueError('Frozen scene cohort mismatch')
    if len(pairs) != 480:
        raise ValueError('Expected 480 pairs')
    for members in pairs.values():
        if len(members) != 2 or {r['condition'] for r in members} != {'original', 'converted'}:
            raise ValueError('Incomplete condition pair')
        for field in ['scene_id', 'target_prim', 'view_id', 'query']:
            if len({r[field] for r in members}) != 1:
                raise ValueError('Paired identity mismatch: ' + field)
    if any(len(objects) != 8 or any(len(views) != 2 for views in objects.values()) for objects in targets.values()):
        raise ValueError('Each scene must have eight targets and two views per target')
    return rows


def validate_files(rows):
    import numpy as np
    from PIL import Image
    for row in rows:
        for kind in ['image', 'mask']:
            if sha(row[kind]['path']) != row[kind]['sha256']:
                raise ValueError(kind + ' hash mismatch')
        mask = np.load(row['mask']['path'], allow_pickle=False)
        with Image.open(row['image']['path']) as image:
            size = image.size
        if size != (1024, 768) or mask.shape != (768, 1024) or mask.dtype != np.bool_:
            raise ValueError('Invalid image or mask dimensions/type')
        if row['condition'] == 'original' and not mask.any():
            raise ValueError('Original qualification requires visible target')


def parse_point(raw):
    match = re.fullmatch(r'\s*Point:\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*', raw)
    return [float(match[1]), float(match[2])] if match else None


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--scenes', type=Path)
    p.add_argument('--protocol', type=Path, required=True)
    p.add_argument('--model', choices=['8b', '32b'], required=True)
    p.add_argument('--checkpoint', type=Path, required=True)
    p.add_argument('--repeat', type=int, choices=[0, 1, 2], required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--mode', choices=['formal', 'qualification'], default='formal')
    p.add_argument('--validate-only', action='store_true')
    a = p.parse_args()
    manifest = json.loads(a.manifest.read_text())
    if a.mode == 'formal':
        if a.scenes is None:
            raise ValueError('Formal cohort manifest required')
        expected = [r['scene_id'] for r in json.loads(a.scenes.read_text())['scenes']]
        rows = validate_structure(manifest, expected)
    else:
        # Existing held-out pilot contract, separate from formal cohort.
        source = Path(__file__).parent.parent / '12_cviu_diagnostics/pilot_inference.py'
        spec = importlib.util.spec_from_file_location('pilot_contract', source)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        rows = module.validate_manifest(manifest)
    validate_files(rows)
    if a.validate_only:
        print('Validated inputs:', len(rows), a.mode)
        return
    protocol = json.loads(a.protocol.read_text())
    model_spec = protocol['models'][a.model]
    if a.checkpoint.name != model_spec['revision']:
        raise ValueError('Checkpoint revision path mismatch')
    import numpy as np
    import torch
    import transformers
    from PIL import Image
    gpu_count = 1 if a.model == '8b' else 2
    if torch.cuda.device_count() != gpu_count:
        raise ValueError(f'Expose exactly {gpu_count} reserved GPUs')
    config = transformers.AutoConfig.from_pretrained(a.checkpoint, local_files_only=True)
    if getattr(config, 'quantization_config', None):
        raise ValueError('Quantized checkpoint forbidden')
    a.out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(__file__, a.out / 'runner_snapshot.py')
    seed = 20261114 + a.repeat
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    model = transformers.AutoModelForImageTextToText.from_pretrained(
        a.checkpoint, torch_dtype=torch.bfloat16, attn_implementation='sdpa',
        device_map='auto', max_memory={i: '40GiB' for i in range(gpu_count)},
        local_files_only=True).eval()
    device_map = getattr(model, 'hf_device_map', {})
    parameter_devices = sorted({str(parameter.device) for parameter in model.parameters()})
    parameter_dtypes = sorted({str(parameter.dtype) for parameter in model.parameters() if parameter.is_floating_point()})
    placement = {'device_map': device_map, 'parameter_devices': parameter_devices,
                 'parameter_dtypes': parameter_dtypes, 'model_device': str(model.device)}
    (a.out / 'placement_report.json').write_text(json.dumps(placement, default=str, indent=2) + '\n')
    if not parameter_devices or any(not device.startswith('cuda:') for device in parameter_devices):
        raise ValueError('Model parameters must reside entirely on GPUs')
    if any(str(v) in ['cpu', 'disk', 'meta'] for v in device_map.values()):
        raise ValueError('CPU/disk/meta offload forbidden')
    if any(p.is_floating_point() and p.dtype != torch.bfloat16 for p in model.parameters()):
        raise ValueError('Unexpected model parameter precision')
    processor = transformers.AutoProcessor.from_pretrained(a.checkpoint, local_files_only=True)
    metadata = {'mode': a.mode, 'model': a.model, 'checkpoint': str(a.checkpoint),
                'revision': model_spec['revision'], 'repeat': a.repeat, 'seed': seed,
                'manifest_sha256': sha(a.manifest), 'protocol_sha256': sha(a.protocol),
                'runner_sha256': sha(__file__), 'torch': torch.__version__,
                'transformers': transformers.__version__, 'device_map': device_map, 'placement': placement,
                'do_sample': False, 'max_new_tokens': 128, 'dtype': 'bfloat16',
                'processor_image_config': processor.image_processor.to_dict(),
                'checkpoint_config_hashes': {}}
    for name in ['config.json', 'generation_config.json', 'preprocessor_config.json', 'processor_config.json', 'tokenizer_config.json']:
        file = a.checkpoint / name
        if file.exists():
            shutil.copy2(file, a.out / name)
            metadata['checkpoint_config_hashes'][name] = sha(file)
    (a.out / 'metadata.json').write_text(json.dumps(metadata, default=str, indent=2) + '\n')
    errors = 0
    with (a.out / 'predictions.jsonl').open('x') as output:
        for row in rows:
            prompt = row['query'] + ' Use normalized 0-1000 coordinates: (0,0) top left, (1000,1000) bottom right. Return exactly one line: Point: x, y'
            result = {**row, 'repeat': a.repeat, 'model': a.model, 'mode': a.mode, 'prompt': prompt}
            start = time.monotonic()
            try:
                messages = [{'role': 'user', 'content': [{'type': 'text', 'text': prompt}, {'type': 'image', 'image': row['image']['path']}]}]
                text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
                with Image.open(row['image']['path']) as im:
                    inputs = processor(text=[text], images=[im.convert('RGB')], padding=True, return_tensors='pt').to(model.device)
                with torch.inference_mode():
                    generated = model.generate(**inputs, max_new_tokens=128, do_sample=False, temperature=0.0)
                raw = processor.batch_decode(generated[:, inputs['input_ids'].shape[1]:], skip_special_tokens=True, clean_up_tokenization_spaces=False)[0]
                point = parse_point(raw)
                valid = point is not None and all(0 <= v < 1000 for v in point)
                mask = np.load(row['mask']['path'], allow_pickle=False)
                ys, xs = np.where(mask)
                hit = bool(mask[int(point[1] * 768 / 1000), int(point[0] * 1024 / 1000)]) if valid else False
                bbox = bool(xs.min() <= point[0]*1024/1000 < xs.max()+1 and ys.min() <= point[1]*768/1000 < ys.max()+1) if valid and len(xs) else False
                result.update(status='ok', raw_response=raw, point_normalized=point, valid_point=valid,
                              hit=hit, visible_bbox_hit=bbox, target_visible=bool(mask.any()),
                              image_grid_thw=inputs['image_grid_thw'].tolist() if 'image_grid_thw' in inputs else None)
            except Exception as exc:
                errors += 1
                result.update(status='runtime_error', error=repr(exc), hit=None)
            result['elapsed_seconds'] = time.monotonic() - start
            output.write(json.dumps(result) + '\n')
            output.flush()
    (a.out / 'completion.json').write_text(json.dumps({'mode': a.mode, 'records': len(rows), 'runtime_errors': errors,
        'status': 'complete' if not errors else 'incomplete_runtime_errors'}, indent=2) + '\n')
    if errors:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
