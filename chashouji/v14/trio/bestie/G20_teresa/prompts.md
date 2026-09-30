# G20 复古歌后（邓丽君式）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 上方，坐在月亮上（月亮是进场载具，画进每一帧）

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G20.png；选的那张回透明底，备选 act_a1_alt.png（品红幕）
外观逐项（80 年代歌后、蓬松短卷黑发、红唇、白底青花旗袍、白高跟鞋）+ "THE SAME big golden crescent moon … exactly the same place, same size and same shape in every cell"，朝右、二郎腿、手空着。
idle 闭眼轻唱、左手捂心口右手向右托掌 / wind 右臂举过头顶、指尖捏着"a small flat thin disc" / throw 手腕往右一弹 / follow 双手合在胸前歪头笑。

## raw/act_b1.png（wave / sing / bow / idle2），参考图 act_a1.png + ref/G20.png；备选 act_b1_alt.png
降下来时：一手扶月尖一手挥手、两腿晃 / 张开双臂仰头唱 / 欠身行礼 / idle。bow 只是做了没进 seq（留作以后离场或待机变化）。

## 月牙镖 raw/crescent_src.png（1024x1024，品红幕）→ web/assets/world/trio_g20_crescent.webp（110x133，cfg scale 0.5）
道具表：月牙镖不做 3D（平面内打转的薄镖，2D 旋转就是它真实的样子）。"拖音符尾"是特效，引擎没有，不做。

## 配准
ref idle，head [155,75,290,200]，fixed = 月亮背弧 [20,40,160,470]，**scale_by fixed**（月亮刚体），anchor 月亮弯里中心 [240,400]，size h 330。残差 0.15 px；bow 低头"头 0.91"是头框伪值。
大小：人（不算月亮）约 2.5 万格内像素 → at.s 0.9 ≈ 2.06 万屏幕像素（上方对 G11）。
