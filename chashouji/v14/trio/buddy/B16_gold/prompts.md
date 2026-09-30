# B16 黄金圣衣战士（2026-10-01）
定妆 ref/B16.png（品红幕）。两张条 2x2、品红幕。
- raw/act_a1.png：idle 格斗架 / wind 右拳收到耳边 / hitA 右拳平伸 / hitB 左拳前伸（模型两格都画成右拳，残影只取前伸的拳头，交替看不出差别）。"NO lightning, NO glow"。另一张 act_a1_alt.png。
- raw/act_b1.png：assemble 张开双臂仰头（圣衣刚合身）/ land 单膝落地 / victory 举拳 / idle2。另一张 act_b1_alt.png。
- frames.json：scale_by sheet；assemble / land 进 loose。配准残差 0.36 px。
- 进场 appear flash 金色，seq 换 assemble → land → victory；出手 rush（光速拳）：残影 = hitA / hitB 前伸拳头（box 在 frames 预览上量），金色速度线，n 6。
- 站位 [820,670,0.85]：s 1 剪影 2.92 万 → 0.85 时 2.11 万；画布宽 960，披风最右伸出锚点 133 px，x ≤ 822；
  同组 B5（wind 举棍过头）在场帧外扩 4px 相交 0，B24 相交 0。
