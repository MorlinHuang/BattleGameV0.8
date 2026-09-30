# G9 广场舞大妈动作条（2026-09-30，generate_image 1024x1536 n2，蓝幕 #0000FF → layers.cut_blue 抠成透明底再进 frames.py）—— 后排地面，模板 C + walk 进场

蓝幕：审查定妆复查定的（丝巾粉花纹被品红键吃掉、衬衫绿叶被绿键吃掉）。原图留 raw/*_blue.png，frames.json 读抠好的 raw/act_a1.png / act_b1.png（透明底）。

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G9.png；备选 act_a1_alt_blue.png
外观逐项（55 岁左右圆润大妈、短烫卷发红花白遮阳帽檐、圆脸红唇、彩色丝巾、扣好的红底黄花衬衫、黑色宽松七分裤、黑布鞋红绣花、腰挂黑色小音箱）、朝右、两脚同一处、手空着。
idle 一手叉腰一手翘兰花指 / wind 右臂抡到脑后上方"about to crack a long ribbon" / throw 右臂直直往上往前甩、手在头顶最高点 / follow 手落到肚子前、另一手叉腰闭眼大笑。红绸不画（引擎 whip 画）。
抠像内部半透明只剩被围住的背景洞（叉腰手臂和腰之间、卷发缝），alpha 都是 0，不是被吃。

## raw/act_b1.png（walk1~walk4，一张图四格，同一张底图），参考图 act_a1.png；备选 act_b1_alt_blue.png
"bouncy Chinese yangge folk-dance walk"：接地 A 远腿在前、右手甩到胸前 / 过渡 A 右膝高抬 / 接地 B 近腿在前、右手甩到身后 / 过渡 B 左膝高抬；左手四帧都叉腰。
摆臂 前 → 中 → 后 → 中。两条腿同色同鞋（审查第六轮第 4 条：没有近远区分时不强制看得出对调）。

## 配准 / 钉脚
ref idle，head [95,10,280,160]，fixed = 两只布鞋 [125,662,255,730]，anchor 鞋底 [190,725]，size h 380；walk1~4 loose。残差 0.64 px。
walkshift.py：loose 帧横向按头对齐，人在四格里前后画得不均（着地鞋跟每次换帧前进 65 / 76 / 59 / 73），把 walk2~4 横移 −3 / +4 / −5 → 68 / 69 / 68 / 68，stride 136.5。
**每次 frames.py build 之后都要重跑 walkshift.py。**
enter.dist 300.3 = 5 × 60.06：不写 dist 时引擎按默认距离 273.8 取整 5 步、每步匀成 54.8，换帧着地脚差 −5.4 px。
