# B26 电竞宅男 动作条（2026-09-30，1024x1536 2x2，参考图 buddy/ref/B26.png；提示词 prompt_a.txt / prompt_b.txt）
- 绿幕（耳机 RGB 灯带有紫粉）。raw/act_a1.png 生图直接回了透明底（alpha 254，四周一圈低 alpha 光晕，黄底检查干净），直接用 alpha。
- raw/act_a1.png：idle（撑脸、右手按沙发前沿像握鼠标）/ wind（右手举过头抡线）/ throw（向左甩出）/ follow（收线到胸前）。
- raw/act_b1.png：pushed（被推着滑、抓沙发边）/ skid（模型多画了一双拖鞋，共四只，不用）/ settle（瘫下伸懒腰）/ idle2。
- 懒人沙发画在帧里，是剪影的一部分：size 按"人 + 沙发"面积对齐樱木（h 217 → 约 3.0 万），所以人比别的地板角色小一圈。
- 道具：3D 鼠标 prop_mouse.webp（引擎道具表的按键版，r 22 cell 88 scale 1.37），线由 atk.tether 画。
- 精美1 方向版（2026-10-01，所需角度 139°）：raw/p6d_swing / p6d_release / p6d_thru，底图都是 wind 格（p6d_*_base.png = p6_swing_base），蒙版 p6d_*_mask.png（swing 底边压到 y≈545 让拳能收到肋下）。
  合成 p6tools/comp_d.py（comp.py 的 p6d 版）+ hair.py 校发色。swing = inpaint-1790856814567-1 绕(600,530)缩 0.92；release = inpaint-1790848891407-2；thru = inpaint-1790848696397-1 绕(520,520)缩 0.98（顶部压回屏幕 y≥1024）。
