# B20 济公式疯和尚（2026-10-01）
定妆 ref/B20.png（品红幕）。两张条 2x2、品红幕；酒坛（红菱形纸签不写字、红布扎盖）和酒葫芦都画在帧里，"the jar is in exactly the same place and same size in every cell"。
- raw/act_a1.png（透明底回来）：idle 挠头、葫芦垂在手里 / wind 仰头灌酒 / throw 鼓腮往前喷（不画雾）/ follow 挥葫芦大笑。另一张 act_a1_alt.png。
- raw/act_b1.png：drift 坛前倾、两腿翘起张臂 / wobble 坛后仰抓坛盖 / settle 坐稳 / idle2。另一张 act_b1_alt.png（settle 嘴边多画了个白气泡）。第一次 502，重试成功。
- frames.json：scale_by sheet，fixed = 酒坛；drift / wobble 坛是斜的，进 loose。配准残差 0.31 px。
- 进场 fly（从右上斜着飘、tilt 0.1）；出手 spray 琥珀色酒雾，from = throw 帧嘴 [30,106]；名单"喷酒雾 + 甩草鞋"二选一取喷（规范第九节建议）。stretch 0.02（默认 0.05 时坛子跟着压扁，读成 2.2 px 漂移）。
- 站位 [860,680,0.8]：s 1 剪影 3.24 万（含酒坛）→ 0.8 时 2.07 万；同组 B2（含 aim 帧）、B28 在场帧相交 0。
