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

## 2026-10-01 月亮拆成挂件层（审查第八批打回 1：月亮每帧重画、月牙尖换帧跳 6.3 px）
不重新生图：`moon.py` 在 frames.py build 出的图集上把月亮从每一帧拿掉，挂件 `web/assets/trio/G20_moon.webp`（226×247）= idle 的月亮，被人挡住的 5587 px 按月牙极坐标（外圆 / 内圆拟合，θ × t 表沿 θ 插值）补。八帧 parts.at 相同，z −1。
- 分割：金色大块（含近白高光）+ 沿金 / 暗金 / 月尖暗橙往外长；深色描边只收贴着透明背景的（人压在月亮上的描边留在人那层）。旗袍金滚边 1~2 px 宽，种子要装得下 3×3，进不来。
- wave 扶月尖的那截前臂生图画成了淡黄（色相 50、饱和 0.25），和高光分不开：KEEP 框里低饱和、色相 < 57.5、跟真正肤色连着的算人。
- 人各帧坐点相对 idle 差 0.4~7.6 格内 px（原来按月亮背弧配准，月亮每帧画得不一样），按臀部 + 大腿平移对齐（余 ≤ 0.16）；cfg hold 的 wind / throw 跟着平移。
- 重新 build 以后必须再跑 moon.py（json 有 moon 字段时拒跑，防止拆两次）。读数 `shots/trio_bestie/月亮挂件_G20_读数.txt`（moon_check.py）。
