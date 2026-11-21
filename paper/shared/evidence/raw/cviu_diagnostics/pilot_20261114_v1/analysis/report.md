# CVIU three-scene pilot

Descriptive three-scene pilot. Repeats are not independent scenes; cross-condition flips are not automatically attributable to materials.

| Repeat | Original hits | Converted hits | Losses | Gains | Flips |
|---|---|---|---|---|---|
| 0 | 11 | 11 | 0 | 0 | 0 |
| 1 | 11 | 11 | 0 | 0 | 0 |
| 2 | 11 | 11 | 0 | 0 | 0 |

## Hit rates and output coverage

[
  {
    "repeat": 0,
    "original_hit_rate": 0.9166666666666666,
    "original_valid_point_rate": 1.0,
    "original_visible_bbox_hit_rate": 1.0,
    "converted_hit_rate": 0.9166666666666666,
    "converted_valid_point_rate": 1.0,
    "converted_visible_bbox_hit_rate": 1.0,
    "flip_rate": 0.0,
    "hit_rate_difference": 0.0
  },
  {
    "repeat": 1,
    "original_hit_rate": 0.9166666666666666,
    "original_valid_point_rate": 1.0,
    "original_visible_bbox_hit_rate": 1.0,
    "converted_hit_rate": 0.9166666666666666,
    "converted_valid_point_rate": 1.0,
    "converted_visible_bbox_hit_rate": 1.0,
    "flip_rate": 0.0,
    "hit_rate_difference": 0.0
  },
  {
    "repeat": 2,
    "original_hit_rate": 0.9166666666666666,
    "original_valid_point_rate": 1.0,
    "original_visible_bbox_hit_rate": 1.0,
    "converted_hit_rate": 0.9166666666666666,
    "converted_valid_point_rate": 1.0,
    "converted_visible_bbox_hit_rate": 1.0,
    "flip_rate": 0.0,
    "hit_rate_difference": 0.0
  }
]

## Same-condition repeat disagreement

{
  "original": {
    "disagreements": 0,
    "comparisons": 36,
    "rate": 0.0
  },
  "converted": {
    "disagreements": 0,
    "comparisons": 36,
    "rate": 0.0
  }
}

## Paired cases

### MVSYCXYKTKJ66AABAAAAADA8_usd:stool:v0
Point to the stool in the image.
Original: [False, False, False]; converted: [False, False, False]
Points (0–1000): {'original': [[496.0, 375.0], [496.0, 375.0], [496.0, 375.0]], 'converted': [[496.0, 427.0], [496.0, 427.0], [496.0, 427.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/16/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/17/rgb.png

### MVSYCXYKTKJ66AABAAAAADA8_usd:stool:v1
Point to the stool in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[477.0, 477.0], [477.0, 477.0], [477.0, 477.0]], 'converted': [[474.0, 375.0], [474.0, 375.0], [474.0, 375.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/18/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/19/rgb.png

### MVSYCXYKTKJ66AABAAAAADA8_usd:toy:v0
Point to the cat in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[476.0, 542.0], [476.0, 542.0], [476.0, 542.0]], 'converted': [[450.0, 540.0], [450.0, 540.0], [450.0, 540.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/20/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/21/rgb.png

### MVSYCXYKTKJ66AABAAAAADA8_usd:toy:v1
Point to the cat in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[437.0, 537.0], [437.0, 537.0], [437.0, 537.0]], 'converted': [[426.0, 527.0], [426.0, 527.0], [426.0, 527.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_early_repairs_v1/04/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_early_repairs_v1/01/rgb.png

### MVUCSQAKTKJ5EAABAAAAAAA8_usd:couch:v0
Point to the couch in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[427.0, 520.0], [427.0, 520.0], [427.0, 520.0]], 'converted': [[437.0, 520.0], [437.0, 520.0], [437.0, 520.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_early_repairs_v1/05/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/01/rgb.png

### MVUCSQAKTKJ5EAABAAAAAAA8_usd:couch:v1
Point to the couch in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[437.0, 500.0], [437.0, 500.0], [437.0, 500.0]], 'converted': [[450.0, 500.0], [450.0, 500.0], [450.0, 500.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_early_repairs_v1/06/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_early_repairs_v1/00/rgb.png

### MVUCSQAKTKJ5EAABAAAAAAA8_usd:laptop:v0
Point to the laptop in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[477.0, 537.0], [477.0, 537.0], [477.0, 537.0]], 'converted': [[500.0, 550.0], [500.0, 550.0], [500.0, 550.0]]}
Center baseline: {'original': True, 'converted': True}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/04/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/05/rgb.png

### MVUCSQAKTKJ5EAABAAAAAAA8_usd:laptop:v1
Point to the laptop in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[478.0, 500.0], [478.0, 500.0], [478.0, 500.0]], 'converted': [[478.0, 528.0], [478.0, 528.0], [478.0, 528.0]]}
Center baseline: {'original': True, 'converted': True}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/06/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/07/rgb.png

### MVUHLWYKTKJ5EAABAAAAADI8_usd:couch:v0
Point to the couch in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[472.0, 527.0], [472.0, 527.0], [472.0, 527.0]], 'converted': [[477.0, 537.0], [477.0, 537.0], [477.0, 537.0]]}
Center baseline: {'original': True, 'converted': True}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/08/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/09/rgb.png

### MVUHLWYKTKJ5EAABAAAAADI8_usd:couch:v1
Point to the couch in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[427.0, 527.0], [427.0, 527.0], [427.0, 527.0]], 'converted': [[427.0, 537.0], [427.0, 537.0], [427.0, 537.0]]}
Center baseline: {'original': False, 'converted': False}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/10/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_v3/11/rgb.png

### MVUHLWYKTKJ5EAABAAAAADI8_usd:microwave:v0
Point to the built-in oven in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[532.0, 532.0], [532.0, 532.0], [532.0, 532.0]], 'converted': [[537.0, 537.0], [537.0, 537.0], [537.0, 537.0]]}
Center baseline: {'original': True, 'converted': True}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_repairs_v1/00/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_repairs_v1/01/rgb.png

### MVUHLWYKTKJ5EAABAAAAADI8_usd:microwave:v1
Point to the built-in oven in the image.
Original: [True, True, True]; converted: [True, True, True]
Points (0–1000): {'original': [[475.0, 575.0], [475.0, 575.0], [475.0, 575.0]], 'converted': [[477.0, 577.0], [477.0, 577.0], [477.0, 577.0]]}
Center baseline: {'original': True, 'converted': True}
Images: /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_repairs_v1/02/rgb.png ; /cpfs/user/zhuzihou/assets/convertasset_research/experiments/cviu/pilot_renders_20261114_repairs_v1/03/rgb.png

