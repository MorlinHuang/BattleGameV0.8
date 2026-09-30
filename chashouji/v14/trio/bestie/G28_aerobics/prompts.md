# G28 80 年代健美操女
槽位地板（站着）、进场 walk（开合跳一路跳进来：bob 20、fps 6；偶数帧接地、奇数帧腾空，stride = 每跳前进距离）、
出手 throw（引擎 3D 呼啦圈 prop_hoop.webp，道具表 r 36 cell 108 scale 1.07）+ onHit wear（套在他头上，要平面图 → 从图集取一格）、**绿幕**（桃红 / 亮紫）。
呼啦圈不画进帧。参考图 ref/G28.png（透明底，铺绿底 /tmp/G28_bg.png）。

## act_a1（idle / wind / throw / follow），1024x1536 2x2
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body standing drawing of THE SAME adult woman as the reference image (big curly brown 80s hair, neon pink terry headband, gold hoop earrings, neon pink high-cut aerobics leotard with yellow and teal stripes, shiny purple tights, striped pink yellow teal leg warmers, white sneakers, wristbands), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she stands in the SAME wide sporty stance facing RIGHT, both feet planted on the ground in exactly the same place and same size in every cell (only arms, head and torso change). Her hands are EMPTY (no hula hoop drawn).
Top-left (idle): left hand on her hip, right arm raised with the index finger pointing up as if twirling a hoop on it, cheerful wink.
Top-right (wind-up): torso twisted back to the LEFT, right arm swung far back low behind her hip as if holding a big hoop like a frisbee, excited grin.
Bottom-left (release): right arm swung forward to the RIGHT fully extended at shoulder height, fingers open as if flinging a frisbee, mouth open cheering.
Bottom-right (follow-through): right fist pumped up in the air, left hand on hip, big smile.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## act_b1（jump1 / jump2 / jump3 / jump4 开合跳循环），参考图 = act_a1 + 定妆绿底
Character animation jumping-jack cycle sheet, 2x2 grid (4 poses), THE SAME woman as the reference sheet, EXACTLY the same character size, costume details and camera distance as the reference sheet, body turned three-quarter toward the RIGHT, hands EMPTY.
Top-left (jump contact A): landed with both feet together on the ground, arms down at her sides, knees slightly bent.
Top-right (jump air A): in mid-air, legs spreading apart, arms swinging up to shoulder height.
Bottom-left (jump contact B): landed with feet wide apart on the ground, both arms straight up overhead in a V, big smile.
Bottom-right (jump air B): in mid-air, legs closing together, arms swinging down to shoulder height.
Head at the same height in all four poses except slightly higher in the two mid-air poses. Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## 实际出图（2026-09-30 08:03 ~ 08:06）
- act_a1 = edited-1790755464397-1（透明底；参考图定妆铺绿底；上面 A 条原文照用），另一张存 act_a1_alt.png。
- act_b1 = edited-1790755562892-2（透明底；参考图 act_a1 铺绿底 + 定妆；上面 B 条原文照用），另一张存 act_b1_alt.png。这张 jump4 两脚离地、并腿，腾空读得出。
- **A 条 follow（握拳举过头）那格头画小了 9%**：按头缩放后整个人放大 1.09，脚踩到地板下 17 px；锁缩放则头比例 0.92。不上场，收势改用 jump3（开腿落地、双臂举成 V 欢呼）。
- `leanK: 0`：两脚大开站定，引擎蓄力后倾绕两脚中点转 0.09 rad，离中点 120 px 的脚上下挪 7.5 px（第一版胶片量出来，改后 0.94）。
- stride 110（格内像素）：每跳前进 55 × s，画外 331 px 约 6 跳，fps 6 → 进场约 1 秒。
