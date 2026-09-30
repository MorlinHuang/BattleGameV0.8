# B18 唐伯虎（2026-09-30，**暂停**：坐墙头进场引擎还没有 appear，帧已出好留着）
- raw/act_a1.png：idle / raise（伸手去背后拿扇）/ wind / throw。raw/act_b1.png：follow / leap / land / idle2。坐在看不见的墙头上（ledge NOT drawn），锚点 = 左手撑着的墙头高度。
- raw/wall.png：墙头瓦檐（挂件层备用，z −1）。扇子挂件层用 ref/B18_fan.png。
- 还没 build。

# 2026-09-30 接着做完（第九节 B18 "是（已开工）"）
- 原有两张条直接 build（scale [0.95, 1.05]），残差 0.98 px。
- 挂件：part.py buddy/ref/B18_fan.png B18_fan w 125（背后斜插的扇子，pivot [38, 87]）；part.py raw/wall.png B18_wall w 330，
  再在瓦檐下接 60 px 白墙面（30 实 + 30 渐隐），做法写在本目录 make_wall.py。两个都是 z −1。
- 进场 appear rise 220、cut 212（墙头那一行）：leap → land(land) → idle。出手 3D 折扇 prop_fan。
