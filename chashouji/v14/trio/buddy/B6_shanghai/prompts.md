# B6 上海滩（2026-09-30，**暂停**：引擎还没有 walk 进场，帧已出好留着，等引擎补上再接）
- raw/act_c1.png：idle / wind（投手式举到耳后）/ throw / follow —— 在用的出手条。
- raw/act_a1.png：idle1 / raise（举手到肩、拇指扣着）/ throw1 / follow1。raw/act_b1.png：walk1 / walk2 / swing / idle2。
- frames.json：fixed 取后脚那只鞋（站着的人后脚钉在地上；出手格前脚会迈出去）。最后一次 build 残差 0.43px，但 wind 头 0.96：
  要把 scale 收到 [0.97, 1.03] 再 build 一次（被叫停时没跑完）。

# 2026-09-30 解禁后重做（第三轮放行，按 B5 后排写法）
- 旧的 act_a1 / act_b1 / act_c1 不再用（b1 只有两帧走路、c1 出手手在耳边不过头顶），留作参考。
- raw/act_a2.png：出手条（参考 ref/B6.png + act_c1）。idle 捏银元 / wind 手垂到胯边拇指扣着 / throw **右臂直举过头顶弹出**（手高过帽顶）/ follow 两指压帽檐。左手全程插兜。
  左下格弹出去的手碰到左上格的鞋，frames.py 切不开 → buddy/relayout.py b6a2 按多边形拆开重排成 raw/act_a2_split.png。
- raw/walk_gen1.png / walk_gen2.png：走路条 3×2（walk 接地 A / 过渡 A / 接地 B / 过渡 B / 停步压帽 / idle）。两次都是同一条腿在前，
  另用单格改图（"把近侧腿换到前面"）试了两张也没换过来；两腿都是黑西裤，换没换画面上看不出，四格取 gen1。
  gen1 的人只有出手条的 0.76 → buddy/prescale.py 放大 1.31 成 raw/walk_gen1_x131.png，frames.py scale 收到 [0.95, 1.05]。
- build 后跑 buddy/walkfix.py B6_shanghai（frames.json walkfix）：四帧横向对齐着地脚，stride 188.5。
