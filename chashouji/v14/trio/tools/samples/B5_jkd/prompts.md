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

## 复审重出走路条（2026-09-30，哥们美术接手 B5 后）
审查第二轮打回：walk1、walk3 同一条腿在前，双节棍在两只手之间跳。
- 生图两次（`raw/walk_gen1.png` 透明底、`raw/walk_gen2.png` 品红幕，2 列 × 3 行：walk1~4 + taunt + idle）。**两次都没按要求对调腿**：
  gen1 两个接地帧都是近侧腿（带外侧黑条）在前，gen2 两个都是远侧腿（纯黄）在前。第二次在提示词里写明"近侧腿露黑条、远侧腿纯黄"也没用。
- 两张合起来正好配齐，拼成 `raw/act_b2.png`（2 × 3，透明底）：
  walk1 = gen1 第 1 格（近侧腿在前，棍在远侧手、随摆臂甩在前）；walk2 = gen2 第 2 格（远侧腿抬起过渡）；
  walk3 = gen2 第 1 格（远侧腿在前，棍在远侧手、摆在身后）；walk4 = gen1 第 2 格（近侧腿抬起过渡）；taunt、idle2 = gen2 第 5、6 格。
  棍四帧都在远侧那只手；两张人高 473~497px，frames.py 按头缩放（scale 放宽到 [0.9, 1.5]，新条人比条 1 小约 25%），头比例 0.99~1.01。
- `enter.stride` 210：walk1 两鞋尖横向距离 197、walk3 233（格内像素）。
- 出手点 `atk.from` [80, 104] → [270, 28]（wind 帧举过头顶的拳头）：`?trioprobe=1` 12 格男生脸框像素全 0（`shots/trio_buddy/B5_复审_出手翻头顶_probe_faces.json`）。
- 验收：`ammoms=40` 胶片同一帧名连续格着地鞋相位相关位移 0.0 px（walk3 × 4 格、walk4 × 3 格），换帧处 8 px（`shots/trio_buddy/B5_复审_走路钉脚_ms40.jpg`）。
- 新 taunt 马步更宽，右脚会碰到同组 B24 的头：`at` 再往后退到 [740, 1070, 0.83]（剪影外扩 4px 逐对相交 0）。

## 走路条第三次：蒙版重绘（2026-10-01，审查_样板 7.2）
上一版（act_b2 = gen1 两格 + gen2 两格拼起来）被打回：远侧脚换帧滑 16~25 px、躯干朝向逐帧来回拧、棍 1 帧在前 3 帧在后。
- inpaint/make_base.py：底 = raw/walk_gen1.png 第一行（walk1 接地、walk4 过渡），行 2 复制一份；蒙版只放开手臂（行 1）/ 腿 + 手臂（行 2），头和躯干锁住；行 3 原 taunt / idle 只给模型看人。
  产物 inpaint/base.png、inpaint/mask.png、inpaint/mask_vis.jpg（蓝 = 重绘区）。
- generate_image（images = base.png，mask = mask.png，n 2）：raw/walk_inp1.png 用；另一张 walk_inp1_rejected.png 背景重画成黑底发光，不用。
  提示词要点："The NEAR arm (sleeve with the black stripe) ALWAYS holds the nunchaku … far hand empty"；逐格写腿：walk3 = plain FAR leg forward、striped NEAR leg behind on toes；walk2 = striped NEAR leg standing、plain FAR leg lifted；过渡帧 "both hands relaxed at the hips, stick hanging along the outer side of the thigh"。
  一次就对：四帧腿、棍都按要求，锁住区（头、躯干）相位相关位移 ≤ 0.7 px。
- raw/act_b3.png = walk_inp1 前两行（walk1 walk4 / walk3 walk2）+ act_b2 第三行（taunt、idle2，上一版审过的）。
- 棍四帧都在近侧手：walk1 后 → walk2 胯边 → walk3 前 → walk4 胯边。
- 钉脚：buddy/walkfix.py 加 edge pivot（整只黑鞋：前脚落地 → 支撑钉鞋跟，支撑 → 后脚踮起钉鞋尖）。只看贴地 16 行时量不到踮起来的后脚，第一版按它对齐后胶片上 walk2→walk3 滑 25 px、walk4→walk1 滑 37 px。
  各帧横移 walk1 0 / walk2 +16 / walk3 +8 / walk4 +17（两次 walkfix 叠加），四次换帧格内位移都是 105，stride 209.5，dist 434.7（5 步，最后一步 walk1）。
  walk1 / walk3 鞋尖距 197 / 228（相差 31，审查 7.2 写的 ≤ 10 没做到）：两张接地帧是模型画的步幅，换帧滑不滑只看"继续着地那只脚"，已经按它对齐（胶片实测 ≤ 1 px）。
- 验收：buddy/shoepin.py 胶片上量鞋跟 / 鞋尖，四次换帧 |Δx| ≤ 1 px（shots/trio_buddy/B5修_走路钉脚与漂移.txt）。
