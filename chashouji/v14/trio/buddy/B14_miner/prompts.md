# B14 方块头矿工（2026-10-01）
定妆 ref/B14.png（透明）。两张条 2x2、品红幕，生图回来一张透明一张品红，都用透明那张。
- raw/act_a1.png：idle 拳头端在身前（拿方块）/ wind 右臂举过头顶托方块 / throw 往前下甩 / follow 双臂举起。另一张 act_a1_alt.png（wind 那格脚位变了）。
- raw/act_b1.png：dig 蹲低一拳往前打（挖墙）/ step 抬膝跨出来 / land 落地两脚分开 / idle2。另一张 act_b1_alt.png。
- frames.json：scale_by sheet；dig / step / land 进 loose。配准残差 0.31 px。
- 进场 appear rise 200 + 灰土色烟（从脚底那条线后面升上来）；出手 3D 泥土方块 prop_dirtblock（r 30 cell 125 scale 1.49），待机也拿在手里（hold.idle），recipe debris。
- 站位 [880,740,0.91]：s 1 时剪影 2.52 万，0.91 → 2.09 万；和同组 B23 在场帧相交 0（B1 是 crew.js 老角色，不在 cast 里）。

## 场景层（2026-09-30，审查第七批打回）
墙面 web/assets/trio/B14_wall.webp 由 ../make_ledges.py 程序画（上沿要精确落在脚底那一行，生图对不齐），cfg parts fixed: true, z: -1。
