# B25 健身教练 动作条（2026-09-30，1024x1536 2x2，参考图 buddy/ref/B25.png）
- 第一张朝向错了（待机前脚在右、朝右跪），作废。重出时写死"front foot planted on the LEFT side, other knee on the RIGHT"。
- raw/act_a1.png：idle（单臂弯举，扭头朝观众）/ raise（举臂）/ throw / follow。follow 格模型把腿画挪了（残差 5.7px），不用。
- raw/act_b1.png：plank / pushup / pop（单膝跪正面秀双臂）/ idle2。
- cfg：待机用 pop（正面秀双臂，朝向干脆）；出手 raise → throw → 原 idle（弯举）当收势。fixed 只框小腿和鞋：俯卧撑那格只有 219px 高，框大了模板比图大、frames.py 直接崩。
- 道具：tools/3d/dumbbell.py（r 24）。
- P6/P7（2026-10-01）：raw/p6_swing（底 raise）/ p6_thru（底 throw）/ p6_idle2（底 pop = 游戏里的待机）。蒙版局部重绘，只取蒙版区贴回底图（腿逐像素不变），条上 scale_as。
  生成图是 1254 透明底且整个人被重画、位置漂 100px+ / 大小 0.665~0.817：按蒙版外的腿模板匹配（搜索窗 ±200px、缩放 0.55~0.96）再贴。
  thru 头被画大 ~10%：腰线以上随高度渐变缩到 0.9（腰处 1）。合成脚本、贴回用蒙版（*_compmask，比生图蒙版略往下扩）在 p6work/（脚本里路径仍写 /tmp/b25）。原 act_b1 第 4 格 idle2 改名 idle0。
- P6 方向版（2026-10-01，所需角度 143°）：raw/p6d_swing / p6d_release / p6d_thru，三张都以 throw 格为底（p6d_*_base 同一张），scale_as throw，替换旧 p6_swing / p6_thru（旧图留着）。
  选用生图：swing /tmp/kf_generated_images/inpaint-1790856748359-1.png，release inpaint-1790848571797-1.png，thru inpaint-1790857082253-1.png。
  合成 p6work/compd.py（贴回蒙版 p6work/p6d_*_compmask），WARP 腰线以上渐变缩：swing/release "0.91 650 600 160"，thru "0.895 650 600 160"（头回到 0.93~1.03，同时把 thru 顶压到屏幕 984 以下）。
  量点（新坐标系 anchor [228.6,346.2]）：P (264,246) R (55,47) S (172,128) thru 手 (37,33)；P→R 136.4°，S→R 145.3°。
