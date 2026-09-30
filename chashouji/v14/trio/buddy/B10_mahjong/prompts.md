# B10 麻将大叔（2026-10-01，第三轮放行后开工）
定妆 ref/B10.png（透明）。品红幕（身上没有粉紫）。
- raw/act_a1.png（参考 ref/B10.png，2x2）：坐在小马扎上（红帆布面、交叉木腿，"the stool and his feet are in exactly the same place"），手空着。
  idle 左手搭膝、右手挠肚皮 / wind 右手捏两张牌举过头顶 / throw 往前下甩、张嘴喊 / follow 双手举起仰头大笑。另一张 act_a1_alt.png。
- raw/walk_gen1.png（参考 act_a1 + ref，2 × 3）：walk1~4 拎折起来的马扎侧身走 + plop 一屁股坐下 + idle。两次都没做到：马扎在 walk3 换到另一只手、walk2 / walk4 抬的是同一条腿。
- 蒙版重绘（同 B5，审查_样板 7.2）：inpaint/make_base.py，底 = walk_gen1 的 walk1（远侧腿在前、近侧手拎马扎在身后）、walk2（近侧腿提起）；
  行 1 右只重绘近侧臂 + 马扎（垂在胯边），行 2 两格重绘腿 + 两臂 + 马扎出 walk3（近侧腿在前、马扎拎在身前）、walk4（近侧腿撑地、远侧腿提起藏在后面）。
  raw/walk_inp1.png 用（透明底），walk_inp1_rejected.png 的 walk4 抬的还是近侧腿。
- frames.json：scale_by sheet（wind 帧头转过去，按头找缩放放大到 1.2 倍）；walkfix edge pivot + shoe blue（蓝人字拖），各帧横移 0 / −13 / −2 / +13，stride 159.5，walk1 / walk3 鞋尖距 158 / 161。
- buddy/cellshift.py：plop 帧在格内往前挪一步（−80 格内 px，格子左边加宽 80）。walk 进场的 seq 只在走路时长里生效，最后一步落地帧画在"离站位差一步"的地方，
  不挪的话坐下后换待机会横跳 66 px。**重新 build 后要依次重跑 walkfix.py、cellshift.py。**
- 出手：3D 麻将 prop_mahjong（r 20 cell 77 scale 1.37），n 2，wind 帧举过头顶那一刻离手（hold.wind [201,8]，头顶 y 62）。
- 站位 [740,1020,0.83]：1040 时和同组 B29 在场帧相交 371 px。
