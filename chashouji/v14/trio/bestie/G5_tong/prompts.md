# G5 客栈老板娘（佟湘玉式）动作条（2026-09-30，generate_image 1024x1536 n2，绿幕 / 回透明底）—— 后排地面，模板 C

旧的 act_a1 / act_b1（暂停前出的，walk 只有两帧、不合四帧规则）改名 old_act_a1.png / old_act_b1.png 留作参考图。

## raw/act_a1.png（idle / wind / throw / follow），备选 act_a1_alt.png
- 第一、二次用 ref/G5_body.png（原样、铺绿底各一次）当参考图都回 422；换成旧的 old_act_a1.png 当参考图、去掉 "lace crop top / high slit / pressed on her chest" 这类词后通过。
- 提示词要点：同一人外观逐项（发髻红花金簪红流苏、玫红宽袖长褙子金花纹、粉上衣、玫红裹裙、红绣花鞋）、"head exactly the same size in every cell"、朝右、两脚同一处；
  不画算盘、手空着。idle 叉腰惊呼 / wind 双手举过头顶"as if holding a wide wooden board horizontally" / throw 双手往右上甩出 / follow 捂领口闭眼叹气。
- 回来是透明底（直接用 alpha）。备选那张 follow 嘴边画了一个"叹气"小符号，不用。

## raw/act_b1.png（walk1~walk4，一张图四格，同一张底图），参考图 act_a1.png，备选 act_b1_alt.png
"walk-cycle sheet 2x2 … sassy exaggerated hip-swaying walk … head and hips at the same height … LEFT hand stays on her hip in all four"；
contact A 左腿在前、右手摆到身后 / passing A / contact B 右腿在前、右手摆到身前 / passing B；"The two contact poses must have DIFFERENT legs in front"。
- 四帧出自同一张图：服装、发簪、流苏、嘴型一致；右手 后 → 中 → 前 → 中（规范 walk 摆臂）。
- 两个接地帧鞋位几乎一样（鞋跟 49 / 168 与 49 / 166），过渡帧着地鞋跟 107：换帧同一只脚差 ≤ 1.5 格内 px，stride 119。

## 配准
- ref idle，head [85,15,215,150]，fixed = 前脚那只鞋 [255,680,360,750]，anchor 鞋底 [306,745]，size h 400；walk1~4 loose。残差 0.23 px，头 0.98~1.01。
- 算盘挂件：part.py ref/G5_abacus.png G5_abacus w 90，pivot = 红绳头 [41,1]，z 1；wind / throw 不画（手里的是 3D 算盘 prop_abacus）。
