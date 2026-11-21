import importlib.util
from pathlib import Path
import tempfile
import unittest

path = Path(__file__).resolve().parents[1] / 'paper/shared/evidence/experiments/12_cviu_diagnostics/inventory.py'
spec = importlib.util.spec_from_file_location('cviu_inventory', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class InventoryTests(unittest.TestCase):
    def test_disjoint_splits_and_missing_conversion(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for family, n in [('home_scenes',24), ('commercial_scenes',13)]:
                for i in range(n):
                    p = root / 'source/scenes/GRScenes-100' / family / 'scenes' / str(i) / 'start_result_raw.usd'
                    p.parent.mkdir(parents=True)
                    p.write_text('#usda 1.0\n')
            a = m.inventory(root/'source',root/'converted')
            self.assertEqual(a, m.inventory(root/'source',root/'converted'))
            counts = {s:sum(r['split']==s for r in a['scenes']) for s in ['pilot','train','validation','test','reserve']}
            self.assertEqual(counts,dict(pilot=3,train=15,validation=5,test=10,reserve=4))
            self.assertEqual(len({(r['family'],r['scene_id']) for r in a['scenes']}),37)
            self.assertTrue(all(r['status']=='converted_entry_missing' for r in a['scenes']))
    def test_insufficient_pool_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                m.inventory(Path(tmp),Path(tmp))
