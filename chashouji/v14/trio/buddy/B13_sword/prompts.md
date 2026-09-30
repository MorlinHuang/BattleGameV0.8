# B13 仙剑少年（2026-10-01）
定妆 ref/B13.png（品红幕；脚下什么都没有，剑由运行时画）。两张条 2x2、1024x1536、品红幕。
- raw/act_a1.png：两脚前后踩在同一条看不见的横线上（"NOTHING is drawn under his feet"），手空着。idle 剑指立在胸前 / wind 剑指举过头顶 / throw 剑指往前点出 / follow 剑指竖在脸前、闭眼得意。另一张 act_a1_alt.png。
- raw/act_b1.png：swoop 俯冲蹲低前倾 / brake 后仰刹住两臂张开 / settle 站直 / idle2。另一张 act_b1_alt.png（settle 两脚并拢，踩不住剑）。
- raw/prop_src.png（横图，参考 act_a1）：上 = 平放的剑（剑尖朝左、无光），下 = 同一把剑 + 蓝光拖尾（拖尾在右）。
  切成 raw/sword_plain.png → part.py w 240 → B13_sword_ride.webp（脚下挂件）；raw/sword_fly.png → part.py w 330 → B13_sword_fly.webp。
- frames.json：scale_by sheet；fixed = 两只脚；swoop / brake / settle 脚位不同，进 loose。
- 脚下的剑：parts z −1，每帧按两只鞋底连线摆（at = 鞋底中点 + 连线角度）。
- 出手：rush 残影，不用 throw。throw 飞出去的平面道具朝向随机（trio.js b.hang），带拖尾的剑会横着 / 倒着飞。
  buddy/B13_sword/add_sword_cell.py 在图集末尾加一格 'sword'（飞剑贴图），rush.ghost 取它，残影按图原样水平画，剑尖一直朝前。
  **重新 build 后要再跑 add_sword_cell.py。** wind 帧用第二个挂件把同一张飞剑画在举起的剑指上方（召剑）。
- 站位 [880,730,1]：剪影面积 2.12 万（上方对格格 2.09 万）；和同组 B7 在场帧外扩 4px 相交 0。
