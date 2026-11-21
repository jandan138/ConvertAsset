"""Download a revision-pinned public checkpoint, recording success or failure."""
import json,time,argparse
from pathlib import Path
from huggingface_hub import snapshot_download,HfApi
parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=4);parser.add_argument('--receipt',type=Path);args=parser.parse_args()
repo='Qwen/Qwen3-VL-32B-Instruct';revision='0cfaf48183f594c314753d30a4c4974bc75f3ccb'
root=Path(__file__).resolve().parents[5];out=args.receipt or root/'paper/shared/evidence/raw/cviu_formal/v1/model_32b_download.json';start=time.time()
try:
 info=HfApi().model_info(repo,revision=revision,files_metadata=True)
 path=snapshot_download(repo_id=repo,revision=revision,cache_dir='/cpfs/user/zhuzihou/models/hf_cache',max_workers=args.workers)
 missing=[s.rfilename for s in info.siblings if not (Path(path)/s.rfilename).is_file()]
 wrong=[s.rfilename for s in info.siblings if (Path(path)/s.rfilename).is_file() and s.size is not None and (Path(path)/s.rfilename).stat().st_size!=s.size]
 result={'repo':repo,'revision':revision,'path':path,'seconds':time.time()-start,'missing':missing,'wrong_size':wrong,'status':'downloaded' if not missing and not wrong else 'incomplete'}
except Exception as exc:result={'repo':repo,'revision':revision,'status':'failed','error':repr(exc),'seconds':time.time()-start}
out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
raise SystemExit(int(result['status']!='downloaded'))
