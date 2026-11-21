import importlib.util,sys
from pathlib import Path
import numpy as np
import json
import pytest

DIRECTORY=Path(__file__).resolve().parents[1]/'paper/shared/evidence/experiments/13_cviu_formal'
sys.path.insert(0,str(DIRECTORY))
spec=importlib.util.spec_from_file_location('formal_statistics',DIRECTORY/'analyze_formal.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def test_cluster_ratio_retains_within_scene_denominators():
    # Scene A has ten supported observations, B only one. Do not average
    # their conditional means or treat repeats as newly sampled scenes.
    indices=np.array([[0,0],[0,1],[1,1]])
    assert np.allclose(m.ratio_draws([0,1],[10,1],indices),[0,1/11,1])


def test_zero_supported_draws_and_degenerate_effect_flag():
    indices=np.array([[0,0],[0,1],[1,1]])
    r=m.summarize_ratio([0,0],[0,1],indices)
    assert r['finite_bootstrap_draws']==2
    assert r['estimate']==0
    assert r['degenerate_bootstrap']


def test_paired_model_resampling_preserves_zero_difference():
    indices=np.random.default_rng(4).integers(0,3,size=(100,3))
    a=m.ratio_draws([0,5,1],[2,5,4],indices)
    b=m.ratio_draws([0,5,1],[2,5,4],indices)
    assert np.max(np.abs(a-b))==0


def test_directional_flips_and_repeat_counts_do_not_cancel():
    refs=[];index={}
    for pair,scene,original,converted in [('a','s0',True,False),('b','s1',False,True)]:
        for condition,hit in [('original',original),('converted',converted)]:
            refs.append({'pair_id':pair,'condition':condition,'scene_id':scene,'mask':{'pixels':1},'center_baseline_hit':False,'uniform_pixel_baseline_probability':.1})
            for repeat in range(3):
                index['8b',repeat,pair,condition]={'hit':hit,'valid_point':True,'visible_bbox_hit':hit,'point_normalized':[100,100] if condition=='original' else [200,200],'hit_on_original_mask':hit,'hit_on_converted_mask':hit}
    scenes,values,repeats=m.components(index,refs,'8b')
    assert scenes==['s0','s1']
    assert values['hit_rate_difference'][:,0].sum()==0
    assert values['flip_rate'][:,0].sum()==6
    assert values['loss_rate'][:,0].sum()==3
    assert values['gain_rate'][:,0].sum()==3
    assert values['original_repeat_hit_disagreement_rate'][:,0].sum()==0
    assert all(r['gains']==1 and r['losses']==1 for r in repeats)


def test_same_point_mask_only_flip_is_not_prediction_score_change():
    a={'hit_on_original_mask':False,'hit_on_converted_mask':True}
    b=dict(a)
    result=m.scoring_components(a,b)
    assert not result['fixed_original_mask_flip_rate']
    assert not result['fixed_converted_mask_flip_rate']
    assert result['prediction_score_component']==0
    assert result['mask_score_component']==1


def test_symmetric_scoring_decomposition_sums_to_observed_delta():
    import itertools
    for oo,oc,co,cc in itertools.product([False,True],repeat=4):
        result=m.scoring_components({'hit_on_original_mask':oo,'hit_on_converted_mask':oc}, {'hit_on_original_mask':co,'hit_on_converted_mask':cc})
        assert result['prediction_score_component']+result['mask_score_component']==int(cc)-int(oo)


def test_run_receipts_reject_seed_and_precision_drift(tmp_path):
    manifest=tmp_path/'manifest.json';manifest.write_text('{}')
    protocol=tmp_path/'protocol.json';protocol.write_text(json.dumps({'models':{k:{'revision':k} for k in ['8b','32b']}}))
    inputs=[]
    for model in ['8b','32b']:
        for repeat in range(3):
            folder=tmp_path/f'{model}_{repeat}';folder.mkdir()
            runner=folder/'runner_snapshot.py';runner.write_text('snapshot')
            meta={'model':model,'repeat':repeat,'mode':'formal','manifest_sha256':m.sha(manifest),
                  'protocol_sha256':m.sha(protocol),'revision':model,'seed':20261114+repeat,
                  'dtype':'bfloat16','do_sample':False,'max_new_tokens':128,'runner_sha256':m.sha(runner),
                  'checkpoint_config_hashes':{},'processor_image_config':{'size':1},'torch':'test','transformers':'test',
                  'placement':{'parameter_devices':['cuda:0'] if model=='8b' else ['cuda:0','cuda:1'],
                               'parameter_dtypes':['torch.bfloat16']}}
            (folder/'metadata.json').write_text(json.dumps(meta))
            (folder/'completion.json').write_text(json.dumps({'mode':'formal','records':960,'runtime_errors':0,'status':'complete'}))
            path=folder/'predictions.jsonl';path.write_text((json.dumps({'model':model,'repeat':repeat})+'\n')*960);inputs.append(path)
    assert len(m.verify_run_metadata(inputs,manifest,protocol))==6
    path=inputs[-1].parent/'metadata.json';meta=json.loads(path.read_text());meta['seed']+=1;path.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='configuration'):m.verify_run_metadata(inputs,manifest,protocol)
    meta['seed']-=1;meta['placement']['parameter_dtypes']=['torch.float16'];path.write_text(json.dumps(meta))
    with pytest.raises(ValueError,match='precision'):m.verify_run_metadata(inputs,manifest,protocol)
