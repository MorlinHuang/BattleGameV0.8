# G25 针筒护士
槽位地板、进场 slide（推输液架滑进来）、出手 throw（巨型针筒，onHit wear 扎在他头上）、绿幕（粉色角色）。
## act_a1（idle / wind / throw / follow）参考图 bestie/ref/G25.png，1024x1536 2x2
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME adult nurse as the reference image (black hair in a ponytail, white nurse cap with a red cross, short pink and white nurse dress with white apron and red cross, white thigh-high stockings, white high heels), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she is in the SAME LOW KNEELING POSE facing RIGHT: right knee up with the right foot planted forward, left knee on the floor, legs and hips in exactly the same place in every cell (only arms, head and torso change). Her LEFT hand always holds the same metal IV drip stand (tall pole with a hanging drip bag, wheeled base) standing upright just BEHIND her on the left. Her right hand is EMPTY.
Top-left (idle): right hand raised beside her face with the index finger up as if tapping a syringe, wink, cheeky smile.
Top-right (wind-up): torso twisted back, right arm pulled far back over her shoulder with the hand gripping as if holding a big syringe like a dart, eyes narrowed.
Bottom-left (release): right arm thrown forward to the RIGHT fully extended at shoulder height, fingers open, mouth open shouting.
Bottom-right (follow-through): right arm swung down across her body, blowing a kiss with a smug face.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.
## act_b1（slide / land / wind / idle2）：一只脚踩在输液架轮座上蹲着滑 / 跳下来跪定 / strong wind-up / idle

## 实际出图（2026-09-30 05:32 服务恢复后）
- act_a1 = edited-1790746547003-1（参考图：定妆铺绿底 /tmp/G25_bg.png —— 透明定妆直接传回 422 一次）。上面 A 条原文改了三处才过：
  "LOW KNEELING POSE" → "LOW CROUCH"、去掉 "short" / "thigh-high"、idle 去掉 "as if tapping a syringe"、wind 改 "fist closed as if about to throw a dart"。
  模型把输液架画在她**前面（右边）**、她左手扶着 —— 出手时手臂从架子前面甩过去，读得清，没重生。
- act_b1 = edited-1790746703136-2（参考图 act_a1 + 定妆绿底）：ride（一只脚踩轮座、一腿后踢、双手握杆）/ hop（跳下来）/ wind2 / idle2。
  提示词："She rides the IV drip stand like a scooter, one foot standing on the wheeled base, the other leg kicked out behind her … hops off the stand to the right …"
  另一张背景出了深色渐变（抠不干净），弃。
- 两张条的 wind 都只是拳头举到肩上，幅度不够大；出手段用 A 条的 wind（蓄力 0.28 秒 → throw 甩到最前，幅度够认）。
