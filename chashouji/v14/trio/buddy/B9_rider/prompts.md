# B9 外卖小哥（2026-10-01，第三轮放行后开工）
定妆 ref/B9.png（品红幕；头盔面罩带粉紫反光 → 动作条用绿幕）。两张条都是 2x2、1024x1536。
- raw/act_a1.png（参考 ref/B9.png）：坐在蓝色小电驴上（车画在帧里，"the scooter in exactly the same place and same size in every cell"），手空着。
  idle 左手扶把、右手竖大拇指 / wind 半站起、右手托过头顶（as if balancing a takeout box on his palm）/ throw 往前下甩、张嘴喊 / follow 两指碰头盔敬礼、眨眼。
  这次生图回来一张绿幕、一张透明底：**绿幕那张轮毂画了绿色高光，被键抠穿（车轮里透底，frames.py 报"轮廓内部被键吃掉 860"）**，留作 raw/act_a1_green_hubkeyed.png；用透明底那张。
- raw/act_b1.png（参考 act_a1 + ref）：cruise 伏低飞驰 / drift 漂移甩尾、右脚点地 / brake 急刹两脚落地、身子前冲 / idle2。另一张备选 raw/act_b1_alt.png。
- frames.json：scale_by fixed（按车身 + 后轮找缩放，头在蓄力时转成正脸、按头找不准），cruise / drift loose。配准残差 0.13 px。
- 出手：3D 外卖盒 prop_takeout（道具表 r 26 cell 96 scale 1.32），wind 帧托过头顶那一刻离手（hold.wind [343,-20]，头顶 y 71），recipe splash（汤汁）。
- 站位 at [625,1062,0.83]：原 [740,1040] 时 wind 举手和同组上方 B11（扒墙 at 952,620）相交 2387 px；往左往下挪到 625,1062 后和 B11、B21 在场各帧外扩 4px 相交 0。
