# G7 黑裙荆棘杀手（约尔式）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 后排地面，模板 C + appear 进场

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G7.png；备选 act_a1_alt.png（品红幕那张，姿势一样）
外观逐项（黑长直、金色玫瑰尖刺发饰、黑色露背高开衩礼服暗红玫瑰纹、黑露指手套、黑过膝高跟靴）、"head exactly the same size in every cell"、朝右、两靴同一处、手空着。
idle 低姿刺客架 / wind 右臂高举过头往后拉、指尖作夹飞刀状 / throw 右臂往右甩出与头同高 / follow 右臂收到身前、左手扶发饰闭眼笑。选的这张回透明底。

## raw/act_b1.png（crouch / rise / emerge / idle2），参考图 act_a1.png + ref/G7.png；备选 act_b1_alt.png
单膝蹲低头（从影子里冒出来）/ 起身撩发冷眼 / 站起张手 / idle。备选那张把光腿画成了黑色连裤袜（服装变了），不用。
crouch 头低着、头发盖脸，按头配缩放只有 0.69 匹配（头读数 1.11）：scale 收到 [0.9, 1.12]，和同一张条的 rise（0.91）同倍数，身子大小一致；
放到 [0.75, 1.2] 会缩到 0.75，人明显小一圈（试过，弃）。

## 飞刀 raw/knife_src.png（generate_image 1536x1024 无参考图，品红幕）
"single elegant throwing stiletto … long thin needle-like silver blade, small gold rose-with-thorns cross-guard, black wrapped grip, gold ring pommel"。
crewart.cut 品红抠 → 180 px 长 → web/assets/world/trio_g7_knife.webp（cfg scale 0.5）。道具表判"飞刀不做 3D"，用平面图打着转飞。

## 配准
ref idle，head [270,15,380,140]，fixed = 前脚高跟靴 [395,590,500,682]，anchor [450,676]，size h 380；crouch / rise / emerge loose。残差 0.19 px。

## 2026-10-01 审查第五批打回：飞刀补描边
- `knife.py`：`raw/knife_180.png`（原 trio_g7_knife.webp）刀身银色像素往白拉 30%，alpha 外扩 3 px 垫 #2a1020 描边 → 186 × 55；cfg scale 0.5 → 0.65（屏幕刀长约 121 px，刀尖最细处连描边约 4.5 px），spin 0 + aim（刀尖朝前直飞）。
- 站位按建议站位_最终：[220, 960, 0.88]。
