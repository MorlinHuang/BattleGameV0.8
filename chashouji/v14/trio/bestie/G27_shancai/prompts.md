# G27 杉菜
槽位地板、进场 slide（冲过来滑铲）、出手 throw（书包，平面道具，盖上贴纯红纸条）、品红幕。书包不画进帧（运行时画在手里）。
## act_a1（idle / wind / throw / follow）参考图 bestie/ref/G27.png，1024x1536 2x2
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME young woman university student about 21 years old as the reference image (shoulder-length straight black hair with blunt bangs, white shirt with rolled-up sleeves, beige knit vest, denim A-line skirt, white canvas sneakers), NOT a school uniform, anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she is in the SAME LOW HALF-KNEEL facing RIGHT: right foot planted forward, left knee on the floor, legs and hips in exactly the same place in every cell (only arms, head and torso change). No bag is drawn. Her hands are EMPTY.
Top-left (idle): left fist on her hip, right hand clenched at her shoulder as if gripping a bag strap, angry pout glaring right.
Top-right (wind-up): torso twisted far back to the LEFT, right arm swung all the way back behind her at hip height as if swinging a heavy bag by its strap, teeth gritted.
Bottom-left (release): right arm swung forward and up to the RIGHT fully extended, fingers opening as if letting go, mouth wide open yelling.
Bottom-right (follow-through): right arm crossed down in front of her body, huffing with puffed cheeks.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no ground, no text, no panel borders.
## act_b1（slide / land / wind / idle2）：棒球式滑铲（一腿前伸、身体后仰）/ 刹住坐起 / strong wind-up / idle

## 实际出图（2026-09-30）
- act_a1 = edited-1790747889830-1（05:58，参考图 ref/G27.png，上面 A 条原文照用）。
- act_b1 = edited-1790748017392-2（透明底；参考图 act_a1 + 定妆），另一张存 act_b1_alt.png。原文：
  "slide tackle: a baseball-style slide along the floor toward the right, right leg stretched straight forward with the sneaker sole leading,
  left leg bent under her, torso leaning far back, left hand trailing on the floor … stopping: the slide braking, right heel digging in,
  pushing herself up with the left hand … strong wind-up … idle"。
- **wind、follow 两帧模型把两腿间距画宽了**（前脚比 idle 靠左 4.4 / 3.7 px）：按后腿配准，前腿用 `fixleg.py` 局部横向拉回（graft 会切掉 follow 压在膝上的拳头），
  build 之后必跑 `python3 v14/trio/bestie/G27_shancai/fixleg.py`。
- 书包用引擎的 3D 转盘（prop_schoolbag.webp，道具表 r 30 cell 115 scale 1.37），没画进帧。
- M_g27_atk 第一次拍（15:55 服务器时间）报 4 个 404：同一时刻另一个角色在往服务器传 B 系列素材和道具（ls -lt 15:55~15:56），重拍两次 0 error。
