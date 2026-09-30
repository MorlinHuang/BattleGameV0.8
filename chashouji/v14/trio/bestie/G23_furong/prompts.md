# G23 郭芙蓉 动作条提示词（2026-09-30，generate_image，size 1536x1024 横图 2x2，品红幕）

## raw/act_a1.png（idle / raise / throw / follow）参考图：bestie/ref/G23.png —— 回了透明底
模板 B（2x2），姿态总述 "SAME DEEP HORSE-RIDING STANCE facing RIGHT … both boots planted in exactly the same place"；
idle 双拳抱腰 / wind-up 双掌收到腰侧后仰（→ 用作 raise）/ release 双掌齐推朝右 / follow-through 一掌在前一掌收腰。

## raw/act_b1.png（slide / land / wind / idle2）参考图：act_a1 + ref/G23.png
Top-left sliding in（低弓步侧滑、双臂后摆）/ Top-right stomp landing（跺进深马步、双臂张开）/ Bottom-left strong wind-up（双掌收到左胯）/ Bottom-right idle。

## 生图之后发现的问题
- 第二张条的人比第一张大一圈、马步也画宽了（靴子差十几 px）：wind / idle2 只留在图集里不上场，出手全用第一张条（raise → throw → follow）。
- fixed 第一版框到格底（y1 525 = 格高），±12 搜索窗被截，全部帧读成 dy −5 并在写 json 时 int64 崩溃；收到 470。
