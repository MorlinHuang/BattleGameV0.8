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

# 2026-10-01 精美1：从 tools/samples/B5_jkd 复制过来（本轮美术只改 v14/trio/buddy/**），之后图集从这里 build；tools/samples 那份是旧样板，不再更新。

## 精美1 P6/P7（2026-10-01）：rush 4 帧循环 hitA → hitC → hitB → hitD + idle2
脚本都在 p6/：base.py（底图，act_a1 原像素格贴 1024² 品红画布、不缩放）、mask.py、paste.py（生成图按腿模板匹配对齐，只取蒙版透明区贴回，渐变 8px）、shrink.py（上半身绕腰点连续形变缩小，不交叉淡化）、headcheck.py。
- hitC（底 hitA，蒙版 y<615 全放开）：头顶举棍、棍水平横在头顶。生成 3 张选 inpaint-1790841525713-1（腿匹配 0.962，缩放 0.810）。头大 4% → shrink 0.96 绕 (660,615)。
  自由那节棍画长了 ~60%（120 vs hitA 74 输出 px）→ 把棍梢一段（raw x 255~305）右移 75、上移 5，中段删掉，长度对上（未缩前存 p6/hitC_longstick.png）。
- hitD（底 hitB，蒙版 y<650，hitB 的棍横在大腿上要一起去）：一节夹远侧腋下、持棍拳收胸前、另一手立掌护脸。生成 2 张选 inpaint-1790844695130-1（腿匹配 0.964，缩放 0.680）。头大 6.4% → shrink 0.94 绕 (610,645)。
- idle2（底 idle，蒙版 = 前手臂框 + 脸椭圆 + 手到鼻子的路径，头发外缘 / 持棍手 / 腿锁住）：拇指擦鼻子 + 坏笑。生成 3 张选 inpaint-1790844879803-3（腿匹配 0.993）。
- frames.json：原 act_b3 末格 idle2 → idle0；加 3 条单格条（scale_as hitA / hitB / idle）；fixed x0 50 → 66：
  新帧前掌 / 棍去掉后最左是前脚，格只留 16px 边，旧框左边多出的 23px 空白在新格里放不下，模板贴边 → idle2 残差 2.33。改后全部 ≤ 0.38。
- build 后 walkfix：stride 209.0，平移 walk1 0 / walk2 +16 / walk3 +7 / walk4 +16。无 cellshift。

## 精美1 返修 p6d hitC（2026-10-01）：棍从头顶降到头侧
combo_scan：老 hitC 棍举到屏幕 y 540，挡住 B13 / B16 认人点。老文件留着（raw/p6_hitC*.png，另备份 p6/old_hitC/）。
- 底 = raw/p6d_hitC_base.png（同 p6_hitC_base，hitA 原像素）；蒙版 raw/p6d_hitC_mask.png 只放开 y 250~614 整行（顶上 250 以上锁成幕布，压住模型往上画）。
- 生成 3 张选 /tmp/kf_generated_images/inpaint-1790848730637-3.png：近侧（黑条袖）手举在耳后、握一节竖着，另一节经链子水平甩向身后（右）齐眼高。
- `P6PRE=p6d python3 p6/paste.py hitC <gen> 640 8`（paste.py 加了 P6PRE 前缀开关，默认 p6 行为不变）：腿匹配 0.933、缩放 0.770。
- 上半身画大：headcheck 头 1.163 倍 → `p6/shrink.py ... 0.835 690 635 60`（未缩存 p6/p6d_hitC_unshrunk.png），复查头 0.971（frames.py 读 0.95，侧脸按头找不准，以 headcheck 为准）。
- frames.json：hitC 那条 src → raw/p6d_hitC.png，其它不动。build 残差全 ≤ 0.41；cell 494×598 → 494×492，anchor [260.9,593.8] → [260.9,487.7]（Δ 0, −106.1）。walkfix stride 209.0（平移 0/16/7/16 不变）。
- at [740,1030,0.83]：hitC 屏幕 x 628.9~885.3、y 638.5~1030.2；棍梢格内 (436,47.5) = 屏幕 (885.3,664.6)；握点 (312,72)。
- 注意：hitD 最高点屏幕 627.7（头发），也高过 636 —— 本轮没要求改。
