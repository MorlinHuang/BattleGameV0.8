# G8 冰雪女王（艾莎式）动作条（2026-09-30，generate_image 1024x1536 n2，绿幕提示词 / 回来是透明底直接用 alpha）—— 后排地面，模板 C + ride 进场

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G8.png；备选 act_a1_alt.png
- 第一次提示词带 "off-shoulder / high leg slit showing her right leg" 回 422；去掉这两处后通过（图里仍然画出了开衩和露肩，和定妆一致）。
- 外观逐项：白金侧麻花辫、冰蓝长裙水晶胸衣、透明淡蓝长披风、水晶高跟鞋；"both feet planted … same place"，朝右，手空着。
  idle 右手向前优雅伸出 / wind 右臂高举过头、掌心朝上"summoning magic above her head" / throw 右臂甩到前方与头同高 / follow 手收到腰前、另一手把辫子撩回去闭眼笑。
- wind 那一格指尖离画布上沿 10 px（没被截，放大看过手指完整）。

## raw/act_b1.png（glide / twirl / stop / idle2），参考图 act_a1.png + ref/G8.png；备选 act_b1_alt.png
"ICE-SKATING toward the RIGHT … gliding gracefully on her heels as if on skates"：燕式单脚滑行（后腿抬平、两臂张开）/ 踮脚转圈（膝抬起、两臂在头上成弧）/ 急停（两脚并拢、身子后仰一手举起）/ idle。
不画冰面、雪花特效（ride 由引擎平移 + 压地细颤）。

## 冰锥 raw/icicle_src.png（1536x1024 无参考图，品红幕）→ web/assets/world/trio_g8_icicle.webp（150x51，cfg scale 0.6，尖朝右 → atk.aim: true 尖朝前直飞）
道具表：G8 冰锥不做 3D（冰的通透感 Toon 渲不出），平面图 + onHit freeze。

## 雪花坠子 raw/snowflake_src.png（1024x1024，品红幕）→ part.py G8_snowflake w 40 → web/assets/trio/G8_snowflake.webp（40x45）
次级摆动：idle 的左手垂着、辫子压在胸前、披风一直拖到地（画不出三边透明的 flex 框），改成指尖下吊一片雪花挂件，挂点上沿 pivot [20,2]，sway 0.35 rad。
冰锥原来想用 idleSpin 在掌心慢转当次级摆动，引擎加了 atk.aim 后拿在手里改成"尖指着他"，不再转，所以另加雪花。

## 配准
ref idle，head [180,15,300,150]，fixed = 前脚水晶鞋 [295,640,372,748]，anchor 鞋底 [338,742]，size h 400；glide / twirl / stop loose。残差 0.46 px，头 0.93~1.01（twirl 仰头转圈 0.93）。
