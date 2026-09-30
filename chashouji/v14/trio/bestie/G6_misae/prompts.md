# G6 平底锅主妇（蜡笔小新妈式）动作条（2026-09-30，generate_image 1024x1536 n2，绿幕 / 回透明底）—— 后排地面，模板 C

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G6.png，备选 act_a1_alt.png
外观逐项（棕色蓬松短卷发、额头红色"井"字青筋、粉色无袖上衣、白荷叶边围裙、黄短裤、粉毛拖鞋）、"head exactly the same size in every cell"、朝右、两脚同一处、手空着。
idle 攥拳怒瞪 / wind 右手高举过头作抓锅柄状 / throw 右臂往右上甩出 / follow 双手叉腰喘粗气（嘴边两团小白气，是漫画符号不是字，保留）。

## 跑步条：raw/walk_base.png（一张图四格，同一张底图）→ raw/act_b1.png（walk3 局部重绘）
- walk_base：参考图 act_a1.png，"run-cycle sheet … contact A 左腿在前、右拳往前 / passing A / contact B 右腿在前、左拳往前 / passing B … The two contact poses must have DIFFERENT legs in front"。
  回来两个接地帧还是同一个姿势（两腿一样的光腿 + 同一双拖鞋分不出远近，两臂也一样：同一只拳在前），直接用就是"每一步都同一只手在前"的跳步。
- 第一次蒙版重绘（整个下半身 + 两臂，蒙版 y ≥ 905）：模型原样画回来，没变。
- 第二次蒙版 `raw/walk3_mask.png`（左下格 y 890~1180：两臂 + 躯干，头和腿不动）：写"近手往前捶、从胸前横过去，远手甩到背后只露拳头"，出来的 walk3 两臂和 walk1 正好相反 → `act_b1.png`。
  腿在蒙版外、一个像素没动，鞋位和底图一致。
- 过渡帧 walk2 / walk4 两拳都在胯边（中）；摆臂 前 → 中 → 后 → 中。

## 配准
ref idle，head [160,15,345,170]，fixed = 前脚拖鞋 [300,665,440,735]，anchor [370,728]，size h 380；walk1~4 loose。残差 0.31 px，头 1.00~1.01。
