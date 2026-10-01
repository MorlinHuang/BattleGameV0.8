# B28 西游胖和尚（八戒式）（2026-09-30，第三轮放行后开工）
定妆 ref/B28.png（透明）。绿幕（猪头是粉的）。提示词原文 prompt_a.txt / prompt_b.txt（b 按规范改成 3x2：walk1~4 + plop + idle）。
- raw/act_a1.png：坐地 idle 捧肚（西瓜）/ wind 双手举过头顶 / throw 往前推 / follow 拍肚笑；背上斜挂九齿钉耙（帧里画）。
  左格背后的钉耙齿碰到右格的鞋 → relayout.py b28a1 拆开成 raw/act_a1_split.png。
- raw/walk_gen1.png（用这张）/ walk_gen2.png：蹲着一扭一扭走四帧 + plop 一屁股坐下 + idle。两腿黑灯笼裤白袜，接地帧换没换腿看不出。
- 头框第一次量到了 idle 格上方的钉耙把上，各帧大小不一；改量帽 + 脸 [205,200,420,345]。
- walkfix：四帧平移 -3 / 0 / -4 / 0，stride 129.5，dist 324 = 5 步（第 5 步是 plop）。

# 2026-10-01 精美1（P6/P7）
- 补 swing / thru / idle2（raw/p6_*.png，蒙版局部重绘，frames.json 单格条 scale_as）；旧 idle2 改名 idle0。
- thru 双手伸得更靠左，图集往左扩 62.7（anchor 176,265）。重 build 后重跑 walkfix：ref 由 walk4 改 walk2（walk4 当 ref 时 walk2 要右移 2 会出格），平移 -5 / 0 / -5 / -2，stride 仍 129.5，dist 324 不变。

# 2026-10-01 精美1 方向版（P6 第二轮，所需角度 138°）
- 新图 raw/p6d_swing / p6d_release / p6d_thru（+_base/_mask）。底图：swing=idle 格、release/thru=throw 格，贴 1024 绿幕画布 (idle@420,400 / throw@410,410)。
  蒙版 = 腰以上 + 左上空白全透明（腿/屁股不透明）。生成图按腿模板匹配对齐后只取蒙版区贴回（脚本 /tmp/b28d/fit.py 思路同 B28 试点）。
- swing 生成图上半身大 ~13%（耳尖距 / 鼻盘）→ 绕胯 (720,760) 缩 0.88，腰线上下 60px 用位移场平滑过渡（不交叉淡化，否则袍边/钉耙重影）。
- release 生成图袍角甩到画布右缘被截、出画 972 → x>925 那段（y 610~715）横向压 0.6，最右 955。
- thru 用的是 release 那一轮的另一张（双臂更高更靠左），生图服务熔断/429 一直没恢复，没单独生 thru。
- frames.json：p6_swing→p6d_swing(scale_as idle)、p6_thru→p6d_thru(scale_as throw)，新增 release 条(scale_as throw)。
- anchor 176,265 → 186.9,303.7（Δ +10.9,+38.7），cell 319x268 → 335x307。walkfix(ref walk2) 平移 -4/0/-4/-1，stride 130.0。
