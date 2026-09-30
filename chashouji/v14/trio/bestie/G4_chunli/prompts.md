# G4 丸子头旗袍格斗家（春丽式）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 后排地面，模板 C

## raw/act_a1.png（idle / wind / hitA / hitB）参考图 ref/G4.png；备选 act_a1_alt.png
2x2 standing sheet，外观逐项：黑发双丸子头 + 白布包子套短白飘带、蓝短旗袍金边金涡纹、白边泡泡袖、金黄腰带、黑色尖刺护腕、白系带战靴、粗壮大腿；
"head exactly the same size in every cell"，面朝右，"LEFT foot (the rear supporting foot) planted in exactly the same place"。
idle 格斗架（右脚在前）/ wind 单腿站、右膝提到胸前 / kick A 右腿垂直高踢、靴子高过头顶 / kick B 右腿平踢到自己头的高度。

## raw/act_b1.png（spin1 / spin2 / land / follow）参考图 act_a1.png + ref/G4.png；备选 act_b1_alt.png
倒立劈叉（水平）/ 倒立斜劈叉 / 翻落低蹲一手撑地 / 同 idle 站位的比 V 眨眼（收势）。

## 配准取舍
- 提示词写的是"左（后）脚不动"，模型实际画成了**后腿踢、站在前脚上**（踢腿格的站脚形状和 idle 的前脚一样、和后脚不一样）。
  第一次 build 用 idle 当参考、fixed 框后脚：踢腿三格站脚匹配只有 0.54~0.60，被拐到小腿上（onion 糊成两个人）。
- 改成 ref = wind、fixed = 站脚那只靴子 [130,535,250,672]、anchor 鞋底 [185,666]：idle / follow 按前脚配上（0.80~0.81），残差 0.38 px。
  物理上成立：格斗架前脚不动、后腿提膝踢出，身子从两脚之间移到前脚上方。
- spin1 / spin2 / land 写 loose（进场帧，脚不在同一处）。
