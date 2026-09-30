# G11 格格 动作条提示词（2026-09-30，generate_image，size 1024x1536，绿幕：粉色角色）

## raw/act_a1.png（待机 / 抬手 / 出手 / 收势）参考图：v14/trio/src/gege.png —— 这张生图直接回了透明底
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME young woman as the reference image (black hair in a Qing-dynasty headdress with a big pink peony and pink tassels, pink peony-print Chinese-style crop top with red frog buttons and gold trim, matching pink tie-side briefs with tassels, barefoot), anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose she SITS SIDEWAYS on the same plain wooden swing seat board, facing RIGHT; the board is in exactly the same place and size in every cell. The swing ROPES ARE NOT DRAWN at all. Her LEFT hand (the one further from viewer) always grips in the air at shoulder height directly above the LEFT end of the board, as if holding a rope. Her right hand is empty (no ball drawn).
Top-left (idle): sitting upright, right hand resting palm-up on her lap as if holding a small ball, legs together hanging down and slightly forward, playful smile.
Top-right (wind-up): leaning back, right arm pulled far back behind her head with bent elbow and open palm, ready to throw, legs lifted forward, mischievous grin.
Bottom-left (release): leaning forward, right arm flung forward and upward to the RIGHT fully extended, palm open, fingers spread, legs kicked forward, mouth open laughing.
Bottom-right (follow-through): body upright again, right arm stretched forward and down, relaxed hand, tongue out cheeky grin, legs hanging.
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

（Top-right 的蓄力不够大——只是举手，留作 raise。）

## raw/act_b1.png（强蓄力 / 收腿 / 伸腿 / 待机）参考图：act_a1 铺绿底 + v14/trio/src/gege.png
Character animation pose sheet, 2x2 grid (4 poses) of THE SAME young woman as the reference sheet (black hair in a Qing-dynasty headdress with a big pink peony and pink tassels, pink peony-print Chinese-style crop top with red frog buttons and gold trim, matching pink tie-side briefs with tassels, barefoot), anime cel-shading, clean black lineart, EXACTLY the same character size, costume details and camera distance as the reference sheet. In every pose she SITS SIDEWAYS on the same plain wooden swing seat board as in the reference, facing RIGHT, board in the same place in every cell. Swing ropes are NOT drawn. Her LEFT hand always grips in the air at shoulder height above the LEFT end of the board, as if holding a rope.
Top-left (strong wind-up): torso twisted and leaning far BACK to the left, right arm swung all the way back behind her body to the LEFT with open palm (the hand is behind her back, far from the face), legs raised forward, eyes locked forward, determined grin.
Top-right (swing back pose): body leaning FORWARD, both lower legs tucked back under the seat board with bent knees, right hand also gripping in the air at shoulder height above the RIGHT end of the board, excited smile.
Bottom-left (swing forward pose): body leaning BACK, both legs stretched straight out forward to the right and up, toes pointed, right hand gripping in the air at shoulder height above the RIGHT end of the board, laughing.
Bottom-right (idle): sitting upright, right hand resting palm-up on her lap as if holding a small ball, legs together hanging down, playful smile (same as the top-left pose of the reference sheet).
Generous empty space between cells, nothing overlaps another cell, nothing cropped.
Background MUST be pure flat chroma green #00FF00 single solid color, no gradient, no shadow, no ground, no text, no panel borders.

## 生图之后发现的问题
- 座板每格长短、位置都不一样（第二张尤其）→ 不能按座板配准；frames.json 用 erase 按木色抠掉，座板和绳子由引擎画，配准改按臀部。
