# G10 粉蓝双马尾坏女孩（小丑女式）动作条（2026-09-30，generate_image 1024x1536 n2，绿幕：发尾有粉色）—— 后排地面，模板 C + ride 进场

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G10.png；备选 act_a1_alt.png
外观逐项（白金双马尾、左边发尾粉右边发尾蓝、黑色尖刺项圈、红蓝袖白短 T、红蓝拼色热裤铆钉腰带、渔网袜、红蓝四轮轮滑鞋）、朝右、两只轮滑鞋同一处、手空着、不画球棒。
idle 右拳举在肩旁"as if resting a baseball bat on her shoulder"、左手叉腰吐舌 / wind 两拳并拢举过头顶往后 / throw 两臂往前上方甩开、手张开 / follow 比 V 眨眼吐舌。

## raw/act_b1.png（cruise / spin / stop / idle2），参考图 act_a1.png + ref/G10.png；备选 act_b1_alt.png（透明底那张）
压低身子冲刺（后脚轮滑抬起）/ 单脚转圈（另一条腿屈膝抬起、两臂甩开）/ T 字横刹后仰两臂张开 / idle。

## 配准
ref idle，head [105,20,215,150]，fixed = 前脚红轮滑鞋 [148,585,265,730]，anchor 两鞋轮子着地中点 [150,727]，size h 390；cruise / spin / stop loose。
**scale_by fixed**：按头找缩放时 wind（仰头）读 0.87、整个人缩一圈（看 preview 明显小），轮滑鞋是刚体，按它找缩放全部 0.96~1.01。残差 0.14 px；
残差表里 wind / spin 的"头 1.11"是仰头 / 转头时头框匹配的伪值（按鞋量人一样大）。
3D 棒球棍用道具表 prop_bat（r 32 cell 98 scale 1.09），帧里不画棍，不存在"帧里画的和 3D 对不上"的问题（审查第六轮第 1 条）。

## 2026-10-01 球棒换 prop_bat_v2 + 待机球棒做成挂件（审查第八批打回：r 32 时 57 px 读成瓶子）
atk r 68、atlas prop_bat_v2（cell 168 scale 1.05，引擎 3566a8a 重渲）。待机：bat_part.py 取图集第 33 格（棍身最竖、粗头朝上）做挂件 G10_bat.webp（78×164，屏幕长边 142 px ≈ 人高 0.4），
pivot = 握把离尾端 13%，挂在 idle 拳头 [228, 88]，z −1（拳头盖住握把），往前倒 16° 让开脸；sway 0.04 rad。idle 的拳头举在下巴前，棍身往后斜靠肩会大半藏在头和马尾后面，所以没照"斜靠肩后"。
已知：挂件不看手里有没有东西，扔出去还在飞时肩上也有一根（待办 14，要引擎认 parts.ammo）。
