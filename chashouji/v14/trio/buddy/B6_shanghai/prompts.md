# B6 上海滩（2026-09-30，**暂停**：引擎还没有 walk 进场，帧已出好留着，等引擎补上再接）
- raw/act_c1.png：idle / wind（投手式举到耳后）/ throw / follow —— 在用的出手条。
- raw/act_a1.png：idle1 / raise（举手到肩、拇指扣着）/ throw1 / follow1。raw/act_b1.png：walk1 / walk2 / swing / idle2。
- frames.json：fixed 取后脚那只鞋（站着的人后脚钉在地上；出手格前脚会迈出去）。最后一次 build 残差 0.43px，但 wind 头 0.96：
  要把 scale 收到 [0.97, 1.03] 再 build 一次（被叫停时没跑完）。
