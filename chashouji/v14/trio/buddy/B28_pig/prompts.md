# B28 西游胖和尚（八戒式）（2026-09-30，第三轮放行后开工）
定妆 ref/B28.png（透明）。绿幕（猪头是粉的）。提示词原文 prompt_a.txt / prompt_b.txt（b 按规范改成 3x2：walk1~4 + plop + idle）。
- raw/act_a1.png：坐地 idle 捧肚（西瓜）/ wind 双手举过头顶 / throw 往前推 / follow 拍肚笑；背上斜挂九齿钉耙（帧里画）。
  左格背后的钉耙齿碰到右格的鞋 → relayout.py b28a1 拆开成 raw/act_a1_split.png。
- raw/walk_gen1.png（用这张）/ walk_gen2.png：蹲着一扭一扭走四帧 + plop 一屁股坐下 + idle。两腿黑灯笼裤白袜，接地帧换没换腿看不出。
- 头框第一次量到了 idle 格上方的钉耙把上，各帧大小不一；改量帽 + 脸 [205,200,420,345]。
- walkfix：四帧平移 -3 / 0 / -4 / 0，stride 129.5，dist 324 = 5 步（第 5 步是 plop）。
