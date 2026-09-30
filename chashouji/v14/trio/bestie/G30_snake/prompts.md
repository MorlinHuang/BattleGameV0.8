# G30 蛇精
槽位地板、进场 slide（蛇形扭滑）、出手 beam（举如意放绿色螺旋光）、品红幕。如意画进帧里（beam 的 drawHeld 在出手后不画 prop，放 prop 会在出手帧消失）。
## act_a1（idle / wind / throw / follow）参考图 bestie/ref/G30.png，1536x1024 2x2
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME adult snake-spirit woman as the reference image (black hair in a tall bun shaped like a rearing snake head, jade green snake-scale long dress with a high slit, gold snake armlets, green eyeshadow, red lips), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she RECLINES ON THE FLOOR facing RIGHT, sitting sideways on her left hip with both legs curled together to the LEFT like a snake tail, supported on her LEFT hand planted on the floor; hips, legs and left hand in exactly the same place in every cell (only her right arm, head and torso change). Her right hand always holds the same short golden ruyi scepter with a green jade head.
Top-left (idle): scepter resting on her shoulder, head tilted, half-closed eyes, sly smile.
Top-right (wind-up): right arm raised high overhead holding the scepter pointing up, torso arched back, fierce eyes.
Bottom-left (release): right arm thrust forward to the RIGHT fully extended, scepter pointing straight to the right, mouth open casting a spell.
Bottom-right (follow-through): scepter lowered in front of her lap, satisfied smirk.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no ground, no text, no panel borders.
## act_b1（slide / land / wind / idle2）：贴地 S 形扭滑 / 撑手坐起 / strong wind-up / idle

## 实际出图（2026-09-30）
- act_a1 = edited-1790748560026-2（06:05，参考图定妆铺品红底 /tmp/G30_bg.png，上面 A 条原文照用）。另一张 act_a1_alt 上下两行贴得太近。
- act_b1 = edited-1790749223311-2（06:22，参考图 act_a1 + 定妆）："slither: lying fully stretched out low along the floor, gliding to the right like a snake,
  body curved in a wavy S shape … slither B: the S curve bending the opposite way … strong wind-up: … right arm swung far back behind her head holding the scepter … idle"。
  这张的 wind2 如意抡到脑后，比另一张（举过头顶，跟 A 条 wind 重复）好；06:07 第一次试 502。
- **A 条左上 idle 那格头画大了 6%**（按脸框量：其余几格对它 0.91~0.94，彼此之间 ±3%）。按头缩放会把其余几格放大 6~19%（身子跟着变大，面积 33k→42k）；
  腿和裙摆的匹配在缩放锁 1 时 0.92~0.98，说明身子本来一样大 —— frames.json 锁 `scale [0.995, 1.005]`，按身子对齐；
  上场待机改用 follow（如意横在膝前），idle 那格不上场。以 follow 为准的头比例：wind 1.00、throw 0.97、wind2 0.97。
