# B25 健身教练 动作条（2026-09-30，1024x1536 2x2，参考图 buddy/ref/B25.png）
- 第一张朝向错了（待机前脚在右、朝右跪），作废。重出时写死"front foot planted on the LEFT side, other knee on the RIGHT"。
- raw/act_a1.png：idle（单臂弯举，扭头朝观众）/ raise（举臂）/ throw / follow。follow 格模型把腿画挪了（残差 5.7px），不用。
- raw/act_b1.png：plank / pushup / pop（单膝跪正面秀双臂）/ idle2。
- cfg：待机用 pop（正面秀双臂，朝向干脆）；出手 raise → throw → 原 idle（弯举）当收势。fixed 只框小腿和鞋：俯卧撑那格只有 219px 高，框大了模板比图大、frames.py 直接崩。
- 道具：tools/3d/dumbbell.py（r 24）。
