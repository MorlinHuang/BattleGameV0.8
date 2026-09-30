# B19 光之巨人 cos 大叔（2026-10-01）
定妆 ref/B19.png（透明）。银红配色，两张条都写绿幕（条 1 回来是透明底，直接用 alpha）。
- raw/act_a1.png：idle 双拳叉腰挺肚子 / wind 两臂张开蓄力 / throw 十字手（竖前臂 + 横前臂成加号，朝左）/ follow 右拳冲天。"NO beams, NO light effects"。另一张 act_a1_alt.png。
- raw/act_b1.png（绿幕）：transform 冲天拳（变身起飞）/ land 深蹲落地 / rise 起身 / idle2。另一张 act_b1_alt.png。第一次 502，重试成功。
- frames.json：scale_by sheet；transform / land 进 loose。配准残差 0.30 px。
- 进场 appear flash 白光；出手 beam（写法同 B22）：蓄力球在胸口计时器（hold.wind [87,128]），光从十字手竖前臂左沿射出（hold.throw [40,86]），白蓝细光线。
- 站位 [850,700,1.06]：s 1 剪影 1.85 万 → 1.06 时 2.08 万；同组 B3（820,1040，含 aim0~10）、B30 在场帧相交 0。
