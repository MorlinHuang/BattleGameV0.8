# B15 白发蒙眼最强（2026-10-01）
定妆 ref/B15.png（透明）。制服黑里带紫调，品红幕会抠坏：条 1 用生图回来的透明底，条 2 用绿幕。
- raw/act_a1.png（2x2，盘腿悬浮、"crossed legs and hips in exactly the same place"）：idle 一手插兜一手搭膝 / wind 食指举过头顶 / throw 往前伸手指一弹 / follow 手指勾起眼罩露一只蓝眼。另一张 act_a1_alt.png（品红幕）。
- raw/act_b1.png（绿幕）：fold 抱臂低头 / reveal 抬头张开双手 / settle 手插兜落定 / idle2。另一张 act_b1_alt.png（reveal 那格手贴到画布右边，被截）。
- raw/orb_src.png（绿幕）：紫色能量球 + 深靛蓝描边外圈（亮底上靠轮廓读出来），part.py w 140 → B15_orb.webp，cfg scale 0.5（屏幕直径 70）。
- frames.json：scale_by sheet，fixed = 盘着的腿和鞋；配准残差 0.20 px。
- 进场 appear flash（紫白）；出手 throw 平面光球（圆的、spin 8 转着飞），wind 帧聚在指尖上方、throw 帧指尖射出；recipe bloom。
- 站位 [880,730,1]：剪影 2.20 万；和同组 B8 在场帧相交 0。
