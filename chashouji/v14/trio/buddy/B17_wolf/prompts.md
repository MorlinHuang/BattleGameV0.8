# B17 补丁帽灰狼（2026-10-01）
定妆 ref/B17.png（品红幕）。两张条 2x2、品红幕。
- raw/act_a1.png："HANGS UPSIDE-DOWN, two feet held together at the TOP as if tied by the ankles (rope NOT drawn)"。idle 抱臂坏笑 / wind 右臂抡到身后 / throw 往左甩出去、张嘴大笑 / follow 搓爪子。一次成（透明底）。另一张 act_a1_alt.png。
- raw/act_b1.png：plunge 伸直俯冲 / bounce 弹回张开手脚 / settle 稳住 / idle2。另一张 act_b1_alt.png。
- raw/net_src.png：捕羊网兜（绳网 + 铁坠 + 绳柄），绳柄贴到画布右边 → net_trim.png 抹掉贴边那截 → part.py w 200 → B17_net.webp（cfg scale 0.7）。
- frames.json：scale_by sheet，fixed = 两条腿（脚踝在上），锚点 = 脚踝（drop 的 line）。配准残差 0.07 px。
- drop 进场：pivot 绳顶 [116,−660]（锚点往上 700 屏幕 px）；在场随绳荡 → 漂移用临时副本页 sway 0 量（B17_M_sway0：0.45 px），正式页 drift.py pivot/rot 模式摆角一档 0.005 rad × 绳长 700 = 3.5 px 量化误差，读数 2.58 不代表漂移。
- 尾巴 flex [150,110,208,198,'l',5,0.9]（flexcheck 上、右、下三边 0）。
- 出手 throw 网兜 + onHit net。名单写的"网住后头上冒一圈小羊"引擎没有，记在 docs/待办.md。
- 站位 [830,370,1.05]：s 1 剪影 1.72 万 → 1.05 时 1.89 万；同组 B10 收势双手举过头顶，y 470 时相交 5223 px，370 时在场帧相交 0。
