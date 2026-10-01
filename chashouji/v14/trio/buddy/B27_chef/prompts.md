# B27 食神 动作条（2026-09-30，generate_image 1536x1024 横图 2x2，参考图 buddy/ref/B27.png）

- raw/act_a1.png：idle / wind1 / throw / follow。弓步低蹲朝左，"feet, hips and legs in exactly the same place"；**NO meatballs and NO skewer**（腰上的牛丸串拆成挂件层 B27_skewer，手里的牛丸是运行时 3D 图集）。
  wind1 格瞄准的手指向右（反了），不用。
- raw/act_b1.png：slide（张臂贴地滑）/ skid（手拍地刹住）/ wind（BIG wind-up）/ idle2。wind 仍画成"捏指在耳边、另一只手往后甩开"，读作回拉蓄力，跟 throw 往前甩对比大，采用。
- raw/skewer.png：竹签串 5 颗牛丸（挂件层，part.py h 80）。
- 头比例：throw 0.94、follow 1.06 是张嘴大喊 / 手指贴脸骗了模板匹配，目测三格头一样大（shots/trio_buddy/B27_头比例目测_idle_throw_follow.jpg）；腿部叠影是一个清楚的影子。
- 道具：tools/3d/meatball.py（r 18，结构密度 27%）。

# P6/P7 补帧（2026-10-01）
- raw/p6_swing.png（底 = act_b1 的 wind 格）/ p6_thru.png（底 = act_a1 的 throw 格）/ p6_idle2.png（底 = idle 格，得意摸下巴）；原 act_b1 第 4 格 idle2 改名 idle0。
- 做法：B28 那种只取蒙版透明区贴回底图 + scale_as。生成图腿和底图逐像素对得上（腿模板匹配 0.99），但**上半身被画大很多**：swing 绕腰带点 (448,586) 缩 0.63、thru 绕 (515,576) 缩 0.81，按帽子面积对齐老帧（±1.5%）。脚本 /tmp/b27/ac.py（腿配准）、sh2.py（上身缩 + 贴回）、clean.py（清碎点）。

# P6 方向版（精美1 第二轮，2026-10-01）：所需角度 128°（往左上 52°）
- raw/p6d_swing.png / p6d_release.png / p6d_thru.png，三张底图都 = act_a1 throw 格（p6d_*_base.png，就是 p6_thru_base），蒙版 = 腰以上全透明（p6d_*_mask.png）；frames.json 三条都 scale_as throw。
- swing：生成图 /tmp/b27d/sw3.png（手捏丸子收在腹前腰侧），绕腰带点 (515,576) 缩 0.77、腰线 600 处 10px 过渡贴回。
- release：三轮。① 直臂往左上 → 肩→手 140°（太平）；② 要求 55° → 128.7° 但指尖超屏幕 y 998 约 34px；③ 要求"前倾、手只到帽顶高" → 手够低但臂 135~145°。
  最终：取③的第 2 张（rg2，缩 0.77）把整条前臂绕肩点 (410,450) 转 −16°（145°→129°，/tmp/b27d/rot.py），再小椭圆蒙版重画腋下接缝（p6d_releaseC_*，生成图 rc2）。
- thru：生成图 th1（上身前压、手臂往左前上 35° 伸到最远、领巾头发往前甩），缩 0.77。因为屏幕上限 y 998，thru 的手没有比 release 更高，只是更远（左 55 px）。
- 头：帽子面积 release 1730 / idle 1817 / throw 1575（−2.4% / +4.8%）；frames.py 打印的头 1.11 是误读（上一轮手量对齐的帧也读 1.11）。
