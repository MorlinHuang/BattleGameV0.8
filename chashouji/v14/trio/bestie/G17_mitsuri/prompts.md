# G17 恋柱（甘露寺式）—— 哥们美术代做，2026-09-30（先建目录占位再开工）
定妆 ref/G17.png（蓝幕）。身上是粉 + 嫩绿，品红、绿幕都会吃头发，只能蓝幕；frames.py 不认蓝幕 → bluekey.py（k = b − max(r,g)，key 40~150，半透明带去溢色）先抠成透明 act_*k.png，再以 screen auto 进 frames.py。

## raw/act_a1.png（idle / wind / throw / follow），参考 ref/G17.png，1024x1536 n2，蓝幕
"HANGS UPSIDE-DOWN, both feet held together at the TOP as if tied by the ankles (rope NOT drawn)"，朝右；手里只握剑柄（粉绿圆镡 + 白柄，NO blade），软剑由引擎 whip 画。
idle 双手合在脸颊边笑 / wind 近侧手抡到身后左边 / throw 同一只手甩到右下 / follow 手伸在右下、另一只手挥、眨眼。选的这张回透明底；备选 act_a1_alt.png（蓝幕）。
## raw/act_b1.png（plunge / bounce / settle / idle2），参考 act_a1_alt.png，n2
伸直俯冲、辫子往上飞 / 弹回张开双臂 / 捧脸稳住 / idle。备选 act_b1_alt.png。
## frames.json
ref idle，head [150,330,270,440]，fixed = 两条腿 [90,20,200,240]，anchor 脚踝 [133,30]，size h 330。
**scale_by fixed**：按头找缩放把第二张条放大了 1.19（倒挂俯冲、张臂的头侧着按头找不准），两条腿每帧都并拢伸直、长度不变，改按腿找后各帧 0.98~1.03，残差 ≤ 0.51 px。
## 数据
drop（len 700，line 脚踝）+ whip（from 剑柄 [236,278]，tip 剑尖），recipe petal（樱花瓣）；flex 左边两根辫子 [90,280,146,338,'t']（右边那根贴着羽织，画不出三边透明的框）。
站位临时 [150,240,1.06]（剪影 1.84 万 × 1.06² ≈ 2.07 万）。
