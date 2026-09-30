# G26 蝴蝶发饰剑士（蝴蝶忍式）
槽位地板、进场 leap（h 小，轻跳落地半蹲）、出手 throw（毒蝴蝶群，3D 转盘 `web/assets/trio/prop_butterfly.webp`，n 多颗）、**绿幕**（紫色蝴蝶羽织）。
蝴蝶不画进帧（运行时从手里放出去）。参考图 `ref/G26.png`（铺绿底 /tmp/G26_bg.png）。

## act_a1（idle / wind / throw / follow），1024x1536 2x2
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME adult swordswoman as the reference image (short black bob hair fading to purple at the tips, a purple butterfly hair ornament, black high-collar uniform jacket with a short black pleated skirt, a white haori with sleeves patterned like butterfly wings in lilac and teal with black veins and white spots, white leg wraps, sandals), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she is in the SAME LOW CROUCH facing RIGHT: right foot planted forward, left knee down on the floor, legs and hips in exactly the same place in every cell (only arms, head, torso and haori sleeves change). No sword is drawn. Her hands are EMPTY.
Top-left (idle): right index finger touching her lips, gentle closed-eye smile, left hand resting on her knee.
Top-right (wind-up): torso twisted back, right arm swept far back behind her with the haori sleeve flaring out like a wing, sly narrowed eyes.
Bottom-left (release): right arm swept forward to the RIGHT fully extended at shoulder height, palm open and fingers spread as if releasing something into the air, sleeve flaring forward.
Bottom-right (follow-through): right hand resting against her cheek, head tilted, sweet smile with eyes closed.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## act_b1（leap / land / wind2 / idle2），参考图 = 铺绿底定妆 + act_a1
Character animation pose sheet, 2x2 grid (4 poses), THE SAME swordswoman as the reference sheet, EXACTLY the same character size, costume details and camera distance as the reference sheet, facing RIGHT, hands EMPTY, no sword.
Top-left (leap): in mid-air jumping lightly to the right, both knees tucked up, arms spread wide so the butterfly-patterned haori sleeves open like wings.
Top-right (landing): just touching down on the right foot, knees bending deeply, arms still spread out for balance, haori fluttering.
Bottom-left (strong wind-up): same low crouch as the reference sheet, torso twisted far back, right arm swept all the way back behind her with the sleeve flaring.
Bottom-right (idle): exactly like the top-left pose of the reference sheet (low crouch, finger on lips).
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## 实际出图（2026-09-30）
- act_a1 = edited-1790747595657-1（05:53，参考图定妆铺绿底 /tmp/G26_bg.png；原文照用；两张都回透明底，这张 wind 袖子往后甩得最开）。
- act_b1 = edited-1790747728074-1（参考图 act_a1 铺绿底 + 定妆），另一张存 act_b1_alt.png。原文见上，landing 改成 "just touching down on the tip of her right foot"。
- 模型没画成"半跪"，画成了"蹲"（两膝都离地）—— 剪影更轻盈，跟"轻跳落地"对得上，没重生。
- 出手用 B 条的 wind2（袖子往后甩得最开）；A 条的 wind 幅度小，没上场。
- 蝴蝶 5 只从同一出手点放出，引擎只给每只弧高 ×0.8~1.2 的随机，飞行中聚成一小团（`F_g26_atk` 格 4~7）；要"一群散开扑过去"需引擎给 n 多颗时加散角。
