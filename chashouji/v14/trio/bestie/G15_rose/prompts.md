# G15 船头红发少女（泰坦尼克 Rose 式）动作条（2026-09-30，generate_image 1024x1536 n2，品红幕）—— 上方，fly 进场

旧 act_a1 / act_b1（暂停前出的，没画船头）改名 old_act_a1.png / old_act_b1.png。

## raw/act_a1.png（idle / wind / throw / follow），参考图 ref/G15.png（定妆里带船头）；备选 act_a1_alt.png
"In every cell the SAME adult young woman … stands on the SAME short white ship bow section: white curved hull deck with a white railing, pointed bow tip on the RIGHT,
section cut off cleanly on the left … exactly the same size, shape and position in every cell, her feet stand on the bow in exactly the same place"。
idle 张开双臂闭眼"飞" / wind 右手高举作拎项链状、眨眼 / throw 右臂往右甩出、探身越过栏杆 / follow 双手捂心口。
**船头画进每一帧**：船头是认人点，定妆时就画在人脚下；每格同一截船头，人站在同一处，配准按两只鞋。

## raw/act_b1.png（grip / step / open / idle2），参考图 act_a1.png；备选 act_b1_alt.png
grip 双手扶栏杆 / step 一脚踩上下横杆 / open 双臂半张 / idle。两张都在 grip、step 两格多画了一根竖栏杆（她扶着的那根），
船头形状跟别的帧不一样，上场会跳 —— 这两格不上场，进场用 follow（捂心口）→ open → idle。

## 配准 / 大小
ref idle，head [230,15,350,150]，fixed = 两只高跟鞋 [290,565,425,640]，anchor [355,630]，size h 400。残差 0.22 px。
人（不算船头）剪影 3.37 万 × (0.75/0.9)² ≈ 2.34 万，对上方样板 G11 2.06 万 +14%（蓬裙大）：at s 0.75。

## 2026-10-01 审查第五批打回：船头做成同一张 + 船尾出画
- `bow.py`（frames.py build 之后跑一次；已加宽过的图集会拒绝再跑）：idle 的船头（低饱和白 / 浅灰、只留长条和大块、外扩 2 px 收描边）垫到 wind / throw / follow / open / idle2；
  每帧拆成 后层（人去掉自己的船头，缝从四周扩散补）→ idle 船头 → 鞋框里的人（鞋在栏杆前）。读数 `shots/trio_bestie/bow_G15.txt`：船头 11961 px 里差 > 12 的 45~84 px（压缩噪声），立柱 x 全是 [62, 203]（改前 56~62 / 188~205 各帧不同）。
- 船尾往左接长 200：顺着甲板斜度（0.25）一列列接出去、立柱按间距 97 复制；图集每格加宽到 562，json 的 cell / anchor / head 跟着 + 200，cfg 格内坐标 + 200。船尾左端到屏幕 x −119。
- 第一版把接长那截做成挂件，combo_scan 把挂件算认人点（G15 在 G7 后面认人点 505 px），改成画进图集。
