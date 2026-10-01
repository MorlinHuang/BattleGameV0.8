# B29 东北卖拐大叔（2026-09-30，第三轮放行后开工）
定妆 ref/B29.png（透明）。品红幕。提示词原文 prompt_a.txt / prompt_b.txt，开工时改了两处：
- 条 a：idle / wind 帧里**画出拐杖**（举着推销、抡过肩），throw / follow 手空了——拐杖是走路、待机的道具，丢出去那根是 3D 图集 prop_crutch。
- 条 b 改成 3x2：拄拐瘸行四帧（walk1 好腿着地、walk2 抬拐、walk3 伤腿着地身子下沉压拐、walk4）+ stop + idle，拐杖始终夹在同一侧。
  用 walk_gen1（gen2 拐杖换了手）。人只有出手条的 0.83 → prescale 1.21。
- walkfix 手写换帧链（过渡帧也是一前一后两脚着地，后脚撑着），平移 +18 / -12 / -9 / -48，stride 118.5，dist 355.5 = 6 步。
- P6/P7（2026-10-01）：raw/p6_swing / p6_thru / p6_idle2（蒙版区贴回底图 + scale_as wind / throw / idle）；条 b 末格改名 idle0。
  swing 合成取膝下原图（y≥870）、头单独放大 1.12；thru 上身被画大 ~1.47，绕胯 (590,655) 缩 0.68。重 build 后 walkfix：stride 118.0，平移 +17 / -12 / -9 / -48。
- 返修（同日）：swing / thru 只重画头（raw/p6_*_headbase.png 右上角贴同比例老帧头作参照、p6_*_headmask.png），贴回时蒙版向上 / 右外扩；thru 头绕颈 (465,478) 缩 0.88。旧版存 /tmp/b29/*_v1.png。
- P6 方向版（2026-10-01，所需 143°）：raw/p6d_swing / p6d_release / p6d_thru 三张都以 throw 格为底（scale_as throw），蒙版=旧 thru 多边形（腿外全重画），底图右上贴老 throw 头作参照、swing 另贴 wind 拐杖作参照。
  swing 生图的拐杖长 1.5 倍且和手不共线 → 擦掉画外那截、把 wind 原拐（413px）按 160.7° 贴到手里、手的皮肤像素压回最上层。
  三帧头都被画小（帽子模板 0.78 / 0.78 / 0.85）→ 头部多边形绕颈点放大 1.28 / 1.28 / 1.18 后复测 1.01 / 0.99 / 0.99。中间文件 /tmp/b29d/。
  P→R 140.0°、S→R 141.1°；build 后 cell 308x358、anchor [193.3, 347.9]；walkfix stride 118.0（平移 +18 / -12 / -8 / -47）。
