# B29 东北卖拐大叔（2026-09-30，第三轮放行后开工）
定妆 ref/B29.png（透明）。品红幕。提示词原文 prompt_a.txt / prompt_b.txt，开工时改了两处：
- 条 a：idle / wind 帧里**画出拐杖**（举着推销、抡过肩），throw / follow 手空了——拐杖是走路、待机的道具，丢出去那根是 3D 图集 prop_crutch。
- 条 b 改成 3x2：拄拐瘸行四帧（walk1 好腿着地、walk2 抬拐、walk3 伤腿着地身子下沉压拐、walk4）+ stop + idle，拐杖始终夹在同一侧。
  用 walk_gen1（gen2 拐杖换了手）。人只有出手条的 0.83 → prescale 1.21。
- walkfix 手写换帧链（过渡帧也是一前一后两脚着地，后脚撑着），平移 +18 / -12 / -9 / -48，stride 118.5，dist 355.5 = 6 步。
