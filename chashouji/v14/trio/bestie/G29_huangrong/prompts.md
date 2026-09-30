# G29 打狗棒女侠（黄蓉式）
槽位地板、进场 leap（撑打狗棒一跃，棒点地荡进来落成蹲）、出手 punch（帧序列版：打狗棒伸缩捅过去，skin 填竹子色）、品红幕。
**定妆已拆层**（规范 6.6）：人 `ref/G29_body.png`、竹棒挂件 `ref/G29_staff.png`（z −1）。
- idle 和进场帧：竹棒由挂件层画（parts.at 逐帧摆），动作条里 **不画棒**（NO bamboo staff）。
- wind / throw / follow：棒拿到手里捅出去 —— punch 从 throw 帧里抠"拳头"，所以这三格**要画一截握在右手里的短竹棒**，
  throw 帧里棒头朝右，fist 框框棒头、wrist 取握棒的手，伸出去的管子 = 竹子色。挂件层这三帧不画（at 不写）。

## act_a1（idle / wind / throw / follow），1024x1536 2x2，参考图 ref/G29_body.png（铺品红底）
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME adult young woman as the reference image (long black hair with two small buns tied with pale green ribbons, gold circlet with a jade gem on the forehead, off-shoulder cream hanfu top with wide sleeves and green cloud-pattern trim, short cream skirt with green sash and a jade pendant, cream boots with green ribbons), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she is in the SAME LOW CROUCH facing RIGHT: right foot planted forward, left knee down on the floor, legs and hips in exactly the same place in every cell (only arms, head and torso change).
Top-left (idle): NO staff drawn, hands EMPTY. Left hand raised behind her shoulder gripping the air as if holding a long pole resting behind her back, right hand reaching forward relaxed, playful grin.
Top-right (wind-up): right hand holds a SHORT GREEN BAMBOO STICK (about arm length, with bamboo joints), pulled far back at her waist like a spear ready to thrust, left palm forward, eyes narrowed.
Bottom-left (release): right arm thrust forward to the RIGHT fully extended at shoulder height, the same short green bamboo stick held horizontally pointing straight RIGHT, mouth open shouting.
Bottom-right (follow-through): the same short green bamboo stick resting on her shoulder, winking with a smug grin.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## act_b1（vault / swing / land / idle2），参考图 = G29_body + act_a1
Character animation pose sheet, 2x2 grid (4 poses), THE SAME young woman as the reference sheet, EXACTLY the same character size, costume details and camera distance as the reference sheet, facing RIGHT. NO bamboo staff is drawn in any pose.
Top-left (vault): in mid-air, body stretched out horizontally, both hands gripping above her head as if holding the top of a tall vaulting pole, legs swinging forward to the right.
Top-right (swing): in mid-air, knees tucked, both hands still gripping above her as if on a pole, about to land.
Bottom-left (landing): landing in a deep crouch, right foot forward, left knee just touching down, one hand touching the floor, hair flying.
Bottom-right (idle): exactly like the top-left pose of the reference sheet.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no ground, no text, no panel borders.
