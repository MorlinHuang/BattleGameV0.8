# G18 挂帅女将（穆桂英式京剧武旦）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 上方，leap 进场

参考图只用人那一层 ref/G18_body.png（规范 4.1 / 6.6），提示词写 "NO feathers, NO back flags, NO spear drawn"；翎子、靠旗由挂件层画。

## raw/act_a1.png（idle / wind / throw / follow），备选 act_a1_alt.png
"Peking opera female general costume: ornate headdress with a red pompom … round golden chest guard, layered armor skirt panels with gold fringe, thick-soled black opera boots"、
"head exactly the same size in every cell"、朝右、两靴同一处。idle 亮相（右膝弯、左腿后伸、左手横胸、右掌推出）/ wind 右手高举到头后作握枪状 / throw 右臂往右掷出 / follow 云手。

## raw/act_b1.png（leap / land / rise / idle2），参考图 act_a1.png；选回透明底的那张，备选 act_b1_alt.png
腾空收腿张臂 / 单膝落地右掌推出 / 起身张臂 / idle。

## 挂件
- `python3 tools/part.py bestie/ref/G18_feathers.png G18_feathers w 133`、`… G18_flags.png G18_flags w 136`：
  宽度 = 定妆拆层里的宽 × (330 / 1424)，330 是 frames.json 的 size（人那一层 idle 高），1424 是 G18_body.png 人的高 —— 跟帧序列同一个比例。
- pivot：翎管插进盔头处（定妆原图 450,795）、靠旗四根旗杆在背后并拢处（390,990），换算到挂件图里。
- 每帧 at：idle 上的位置用 idle 头框在缩放后的定妆图里做模板匹配定出（0.80），其余帧 = idle 位置 + 这一帧的头相对 idle 的位移（头模板匹配）。合成预览检查过八帧翎子都从盔头长出来、靠旗都在背后。

## 配准 / 大小
ref idle，head [135,15,285,150]，fixed = 前脚厚底靴 [340,520,455,620]，anchor [400,615]，size h 330；leap / land / rise loose。残差 0.17 px。
人那一层 idle 剪影 2.80 万，at s 0.88 → 2.17 万（上方样板 G11 2.06 万）。
