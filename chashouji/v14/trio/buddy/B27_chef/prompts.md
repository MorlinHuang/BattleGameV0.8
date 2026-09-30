# B27 食神 动作条（2026-09-30，generate_image 1536x1024 横图 2x2，参考图 buddy/ref/B27.png）

- raw/act_a1.png：idle / wind1 / throw / follow。弓步低蹲朝左，"feet, hips and legs in exactly the same place"；**NO meatballs and NO skewer**（腰上的牛丸串拆成挂件层 B27_skewer，手里的牛丸是运行时 3D 图集）。
  wind1 格瞄准的手指向右（反了），不用。
- raw/act_b1.png：slide（张臂贴地滑）/ skid（手拍地刹住）/ wind（BIG wind-up）/ idle2。wind 仍画成"捏指在耳边、另一只手往后甩开"，读作回拉蓄力，跟 throw 往前甩对比大，采用。
- raw/skewer.png：竹签串 5 颗牛丸（挂件层，part.py h 80）。
- 头比例：throw 0.94、follow 1.06 是张嘴大喊 / 手指贴脸骗了模板匹配，目测三格头一样大（shots/trio_buddy/B27_头比例目测_idle_throw_follow.jpg）；腿部叠影是一个清楚的影子。
- 道具：tools/3d/meatball.py（r 18，结构密度 27%）。
