# B21 樱木 动作条提示词（2026-09-30，generate_image，size 1024x1536）

## raw/act_a1.png（待机 / 蓄力 / 出手 / 收势）参考图：v14/trio/src/sakura.png
Character animation pose sheet, 4 rows stacked vertically, each row one full-body pose of THE SAME character as the reference image (red buzz-cut hair, black basketball jersey number 7 with red trim, black shorts with red stripes, white socks, red-black sneakers), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in every row. In every row he LIES ON HIS BELLY on the floor facing LEFT, legs stretched out to the right, hips and legs in exactly the same place in every row (only arms, head and chest change). His hands are EMPTY (no ball drawn).
Row 1 (idle): propped up on both forearms, chest slightly raised, both hands cupped together in front of his chin as if holding a ball, cocky grin.
Row 2 (wind-up): chest raised high, right arm pulled far back over his head with bent elbow and open palm (ready to hurl something), left forearm on the floor, gritted teeth, eyes fierce.
Row 3 (release): right arm whipped forward and fully extended to the LEFT at head height, palm open and fingers spread, chest lunging forward, mouth open shouting.
Row 4 (follow-through): right arm hanging down forward past his head with relaxed hand touching the floor, chest back down on the floor, big satisfied grin.
Rows separated by generous empty space, no character overlaps another row, nothing cropped by the image border.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no floor line, no text, no panel borders.

## raw/act_b1.png（腾空扑 / 砸地 / 滑行 / 待机）参考图：raw/act_a1.png + v14/trio/src/sakura.png
Character animation pose sheet, 4 rows stacked vertically, each row one full-body pose of THE SAME character as the reference images (red buzz-cut hair, black basketball jersey number 7 with red trim, black shorts with red stripes, white socks, red-black sneakers), anime cel-shading, clean black lineart, same character size, same costume details, same camera distance as the reference sheet. He always faces LEFT, body horizontal, head on the left, feet on the right. Hands EMPTY.
Row 1 (dive, airborne): flying horizontally through the air like a superman dive, both arms stretched straight forward to the left, body straight and level, legs together behind, determined shout, a little space under him (he is in the air).
Row 2 (belly-flop impact): chest and belly just slammed onto the floor, both arms forward on the floor, lower legs kicked up behind him bent at the knees, eyes squeezed, teeth gritted.
Row 3 (sliding): lying flat on his belly sliding forward, both arms stretched forward on the floor, head up, feet slightly lifted, grinning.
Row 4 (idle): propped up on both forearms, chest slightly raised, both hands cupped together in front of his chin as if holding a ball, cocky grin (exactly like row 1 of the reference sheet).
Rows separated by generous empty space, nothing overlaps another row, nothing cropped by the image border.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no floor line, no motion lines, no text, no panel borders.

## 生图之后发现的问题
- act_a1 的 Row 3（出手）腿被画短了一截：短裤对齐后鞋尖差 20px（frames.py check 报出来），用 graft 从 wind 移植。
