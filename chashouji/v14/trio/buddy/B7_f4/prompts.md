# B7 卷发大少（2026-09-30，第三轮放行后开工）
定妆 ref/B7.png（透明）。绿幕（酒红丝绒离品红近）。两张条都是 2x2。
- raw/act_a1.png（参考 ref/B7.png）：站在黑色双轮电动平衡车上（LED 蓝轮圈，车画在帧里）。idle 左手插兜、右手伸直指人 / wind **右手捏着纸条举过头顶** /
  throw 从头顶往前下甩、张嘴 / follow 抱臂扭头。提示词要点："STANDS on a black two-wheeled self-balancing hoverboard scooter ... the hoverboard in exactly the same place and same size in every cell ... His hands are EMPTY (no paper drawn)"。
- raw/act_b1.png（参考 act_a1 + ref）：cruise 插兜后仰滑行 / swerve 拐弯撩头发 / brake 急刹后仰两臂张开 / idle。
- raw/prop_src.png：红纸条（长条、金边、两头微卷、不写字），part.py → web/assets/trio/B7_redslip.webp（onHit wear 挂在她头上）。
- 进场 ride：cruise → swerve → brake(land)；出手在 wind 帧举过头顶那一刻离手（fire 段仍是 wind）。

# 2026-10-01 精美1
- P6/P7：补 swing / thru / idle2（raw/p6_*.png，蒙版局部重绘）；旧 idle2 改名 idle0。
- 红牌重画：raw/prop_src2.png（红纸白字「红牌」、两头卷边、金边），part.py h 140 → B7_redslip.webp（126×140），cfg scale 0.55。旧图 prop_src.png 留着。
