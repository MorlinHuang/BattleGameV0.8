# B5 截拳道 动作条提示词（2026-09-30，generate_image，size 1024x1536，n 2 挑一张）—— 后排地面样板（规范 4.1 模板 C）

## raw/act_a1.png（待机 / 蓄力 / 连打 A / 连打 B）参考图：v14/trio/buddy/ref/B5.png
Character animation pose sheet, 2x2 grid (4 poses), each pose one full-body standing drawing of THE SAME young martial artist as the reference image (black bowl-cut hair with bangs, bright yellow one-piece jumpsuit with a black stripe down each side of the body, arms and legs, black kung-fu slip-on shoes), generic anime face, anime cel-shading, clean black lineart, identical character size, identical costume details and identical camera distance in all four poses. In every pose he stands in a low martial-arts stance facing LEFT, both feet planted on the ground in exactly the same place and same size in every cell (only arms, head, torso and the weapon change). He holds a pair of black wooden nunchaku (two short black sticks joined by a short silver chain) in his right hand.
Top-left (idle): classic fighting stance, left open palm forward, right fist raised near his cheek holding the nunchaku with the other stick tucked under his right armpit, calm fierce stare.
Top-right (wind-up): torso twisted back to the right, right arm raised high behind his head whirling the nunchaku (one stick in hand, the other stick swinging up behind him), left palm guarding forward, gritted teeth.
Bottom-left (strike A): lunging forward, right arm fully extended to the LEFT at head height, nunchaku stick whipped straight out forward to the left, mouth wide open shouting a battle cry.
Bottom-right (strike B): backhand low strike, right arm swept across his body down to the left at waist height, nunchaku stick flying out low to the left, left fist pulled back at his hip, shouting.
Generous empty space between cells, nothing overlaps another cell, nothing cropped by the image border.
Background MUST be pure flat magenta #FF00FF single solid color, no gradient, no shadow, no ground line, no motion lines, no text, no panel borders.

## raw/act_b1.png（走路循环 3 帧 + 摸鼻子收势）参考图：raw/act_a1.png + v14/trio/buddy/ref/B5.png
Character animation walk-cycle sheet, 2x2 grid (4 poses), each pose one full-body drawing of THE SAME young martial artist as the reference sheet (…同上外观…), generic anime face, anime cel-shading, clean black lineart, EXACTLY the same character size, costume details and camera distance as the reference sheet. In every pose he is WALKING toward the LEFT in side view (three-quarter view like the reference), a confident swaggering walk, head and hips at the same height and same horizontal position in every cell (only the legs and arms change). He holds the black nunchaku in his right hand, the other stick hanging down from its short silver chain beside his right thigh.
Top-left (walk contact A): his LEFT leg stepping forward to the left with heel touching the ground, right leg behind on its toes, left arm swinging back.
Top-right (walk passing A): his weight on the left leg straight under his hips, right knee bent passing forward, arms close to his body.
Bottom-left (walk contact B): his RIGHT leg stepping forward to the left with heel touching the ground, left leg behind on its toes, left arm swinging forward.
Bottom-right (taunt / follow-through): standing in the same fighting stance as the top-left pose of the reference sheet, nunchaku resting over his right shoulder, left thumb flicking his nose, cocky smirk.
（背景同上）

## 生图之后发现的问题
- 条 2 两张里另一张背景是黑底 + 发光晕，抠不干净，没用。
- 条 2 第二格（walk2）后脚鞋口多画了一块红（原图没有）：`raw/act_b1_fix.png` = 把 (770~835, 560~635) 里偏红的像素按亮度改成鞋的黑色，frames.json 用 fix 这张。
- 第一次 build 用两只脚一起当 fixed，hitB 残差 5 px（模型把两脚间距画得不一样）→ fixed 只框承重的前脚 `[50,600,250,700]`，残差 ≤ 1（各帧同一个 −1 的系统偏差，帧间差 ≤ 0.5）。
- hitA 后脚往前迈了 15 px：是动作，不是走样，不 graft。
- 连打残影框第一版带进了黄袖子（飞出去是一团黄色），收到只框棍子：hitA `[0,85,125,122]`、hitB `[75,195,190,232]`。
