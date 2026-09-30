# G13 白衣古墓仙子（小龙女式）动作条（2026-09-30，generate_image 1536x1024（横图）n2，品红幕）—— 上方，rope 进场（绳子引擎画）

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G13_body.png（定妆拆出来的人层）；备选 act_a1_alt.png（wind 手里画了一截白绸，会和引擎的 whip 叠成两份，不用）
外观逐项（黑长直白发带、白色层叠汉服长纱袖、飘带、赤脚）；"RECLINES in mid-air on her back as if lying on an invisible horizontal tightrope at her hips … NO ROPE IS DRAWN"，头左脚右、朝右、腰臀同一处、手空着。
idle 一手枕头一手搭在屈起的膝上 / wind 支起一肘、另一手举过头捏着绸带 / throw 往右甩 / follow 躺回去撩头发。
规范 6.6 说 G13 用 layers.py rope_layer() 画整绳做挂件；这里改用 rope 进场写法自带的引擎绳（ends / touch / sag，画在人之下，黄褐 #b98a4e、描边 #5a3a1a、w 6），
帧里不画绳，就没有"绳子从腿前 / 腿后过"的洞要扣。

## 进场只用这一张条
rope 滑进来时用 follow（躺着撩头发），到位换 idle（露面后两个姿态）。

## 配准
ref idle，head [140,20,225,120]，fixed = 伸直的那条腿 + 脚 [440,175,745,248]，anchor 腰臀压绳那一点 [360,232]，size w 400。残差 ≤ 2.00 px（follow）。
剪影含垂发和绸带约 4.8 万格内像素 × 0.66² ≈ 2.1 万（上方对 G11）。
漂移：rope 在场整个人按解析式晃（trio.js 249~253），量换帧要临时 sway 0 拍（*_sway0，已换回）。
