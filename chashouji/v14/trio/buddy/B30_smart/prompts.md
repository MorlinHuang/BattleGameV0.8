# B30 杀马特 动作条（2026-09-30，1024x1536 2x2，参考图 buddy/ref/B30.png）
- raw/act_a1.png：idle（跪地捂半脸）/ wind / throw / follow（手插头发）。raw/act_b1.png：kneeslide / arrive / stop（指天）/ idle2。
- 只做飞梳子（名单：发胶喷雾引擎缺 spray）。梳子 comb.py 程序画（生图服务 503），prop_comb.webp，scale 1.4。
- follow 头比例 1.08：手插进头发盖住头框，目测一样大。
- P6/P7（2026-10-01）：swing / thru / idle2 局部重绘补帧（底图 wind / throw / idle，品红幕）。p6base.py 出底图、p6mask.py 出蒙版、
  p6paste.py 按腿配准生成图 → 上半身绕胯缩（swing 0.90 / thru 0.85，生成图上半身画大了）→ 只取蒙版透明区贴回。原 idle2 改名 idle0。
  生成图：swing inpaint-1790844753612-2、thru inpaint-1790844661062-2、idle2 inpaint-1790844911746-1（/tmp/kf_generated_images）。
- P6 方向版（2026-10-01，所需 140°）：p6dprep.py 出底图/蒙版，p6dpaste.py 贴回（PADR=160 给 swing 右侧加宽，手伸出 1024 画布）。
  swing 生图用 raw/p6d_swing_mask_gen.png（保留原 wind 头发椭圆），贴回用 raw/p6d_swing_mask.png（腰以上全换）。
  swing inpaint-1790849214397-2（f 1.0）、release inpaint-1790848932787-3（f 0.87）、thru inpaint-1790849079978-2（f 0.88）。
  量点（新格内输出像素）：P(351,256) R(32,34) S(148,112) thru 手(56,44)；P→R 145.2°、S→R 146.1°。对比图 p6dcmp.py。
