# G16 狐尾妖姬（妲己式）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 上方，九尾宝座画进每一帧

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G16.png；备选 act_a1_alt.png
外观逐项（黑长直狐耳、金钗流苏、红金古装长袖、金饰、红高跟）+ "THE SAME throne of nine big fluffy white fox tails with golden tips … same place, same size and same shape in every cell"，朝右、二郎腿、手空着、不画火。
idle 右手向右托掌"as if a small flame floats above it" / wind 右臂举过头顶托掌 / throw 右臂向前甩开五指 / follow 长袖掩嘴笑。

## raw/act_b1.png（wrap / stretch / lean / idle2），参考图 act_a1.png + ref/G16.png；备选 act_b1_alt.png
尾巴裹住身子只露眼睛和狐耳 / 伸懒腰 / 托腮侧倚斜眼笑 / idle。appear 淡入那 0.35 秒用 wrap，淡入完 stretch → lean → idle。

## 狐火 raw/foxfire_src.png（品红幕）→ web/assets/world/trio_g16_foxfire.webp（100x109，cfg scale 0.45）
名单写"青蓝狐火球"；画成三道火舌风车状的圆球：拿在手里 idleSpin 转、飞的时候 spin 转都读成"火在打旋"，不像一张图在转。道具表：狐火不做 3D。

## 配准
ref idle，head [240,40,345,190]，fixed = 交叠的大腿 + 臀 [200,330,420,480]，anchor 最低点 [300,700]，size h 360；wrap loose。
**scale_by sheet**：按头逐帧找缩放时 wind（仰头）放大到 1.15、stretch 缩到 0.85（yellow 预览一眼看得出大小不一），改成每张条只在它的 idle 格找一次。残差 0.27 px。
大小：人（不算白尾巴）约 3.2 万格内像素 → at.s 0.8 ≈ 2.05 万屏幕像素（上方对 G11）。
漂移框要挨着锚点（两只红鞋）：量大腿框时呼吸（绕锚点竖向胀缩）+ leanK 读进 ±2 px。
