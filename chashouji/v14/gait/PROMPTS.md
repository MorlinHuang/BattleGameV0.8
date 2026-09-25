# 步态帧生图 prompt（蒙版局部重绘）

每档：images=[gait/<档>/base.png]，mask=gait/<档>/mask.png，size=1536x1024，n=2。
**现行八格**（f1~f7）用下面「八格版 PHASE」三句，每句出两张：f1/f5 = LIFT-OFF，f2/f6 = PASSING，f3/f7 = REACH；f4 = 两腿换位（沿用旧 p3，旧模板 p3 那句）。
旧四格版（p2/p3/p4）的说明保留在后面。
p2 = 前腿（靠近对方那条）抬起往后收；p3 = 两腿换位站定；p4 = 另一条腿抬起往后收。
a 档（aK aF aL）重画女生的腿，往左倒走；b 档（bK bF bL）重画男生的腿，往右倒走。
挑图：品红底占比正常（不是黑底）、腿接得上胯、脚在原地面线、朝向没转。

模板（{WHO} {DIR} {SHOES} {PANTS} {PHASE} 按下表替换）：

Inpaint ONLY the transparent masked area (the legs of {WHO}). Everything outside the mask must stay pixel-identical: same upper body, same arms, same phone, same other person.
This is one frame of a WALKING-BACKWARD cycle: {WHO} is pulling the phone and walking BACKWARD toward the {DIR} edge of the image, step by step, while still facing the opponent. {PHASE}
IMPORTANT: the body does NOT turn around — hips, knees and toes still point toward the opponent; walking backward, not away. Keep {SHOES}, {PANTS}, same leg length and proportions, the hips connect seamlessly to the unchanged upper body, feet on the same floor line as the reference.
Style: flat 2D cel-shaded cartoon, thick black outlines, flat color fills, same as the reference. Background: solid flat magenta #FF00FF, no shadow, no floor, never black, never dark.

| | a（女） | b（男） |
|---|---|---|
| WHO | the girl in pink bunny pajamas on the LEFT, facing RIGHT | the young man in white T-shirt and black track pants on the RIGHT, facing LEFT |
| DIR | LEFT | RIGHT |
| SHOES | the same white bunny slippers | the same black cat slippers |
| PANTS | the same pink pajama pants | the same black track pants with white side stripes |

PHASE：
- p2: PASSING pose: the rear leg (farther from the opponent) is firmly planted and bearing weight; the FRONT leg (closer to the opponent) is lifted off the floor, knee bent, foot swinging backward past the planted leg, mid-step.
- p3: CONTACT pose with LEGS SWAPPED compared to the reference: the leg that was in front is now planted BEHIND (farther from the opponent), and the other leg is now the front leg; both feet on the floor, wide leaning-back stance.
- p4: PASSING pose with the OTHER leg: the front leg is planted under the hips bearing weight; the rear leg is lifted off the floor, knee bent, swinging backward to take the next step, mid-step.

八格版 PHASE（开头改成 "Keep the ENTIRE image exactly as the reference, including the flat solid MAGENTA #FF00FF background. Inpaint ONLY the transparent masked area: redraw the legs of {WHO} on the same flat magenta background."，中间 "One frame of a smooth WALKING-BACKWARD cycle (walks backward toward the {DIR} edge, still facing the opponent)."）：
- LIFT-OFF: one foot is planted flat on the floor slightly BEHIND the hips, bearing weight; the other foot is out in FRONT and is just peeling off the floor — heel raised, only the toes still touching, knee starting to bend. Small, natural step, not a big kick.
- PASSING: one foot is planted flat on the floor DIRECTLY UNDER the hips, that leg nearly straight and vertical, bearing all the weight; the other leg is lifted, knee bent, its foot a little off the floor right next to the planted ankle, swinging past it toward the back.
- REACH: one foot is planted flat on the floor slightly IN FRONT of the hips, leg angled, bearing weight; the other leg is extended BACKWARD, knee almost straight, its foot low and about to touch down on the floor behind (toes just above the floor).
（"BEHIND/IN FRONT" 后面要写明是画面的左还是右：女生往左退，身后 = 左；男生往右退，身后 = 右。）

## 换装（2026-09-25，女 A 粉吊带短裤 / 男 B 敞开浅蓝睡衣 + 藏青短裤）
关键姿势：`generate_image images=[旧姿势, outfit/n0_new.png]`（第二张只当服装参考），prompt 开头 "Image 1 is the frame to edit; image 2 is the OUTFIT reference only (ignore its poses). Keep image 1 EXACTLY …"，姿势基本不走样。旧衣服的图在 `*/old_outfit1/`。
步态 WHO / PANTS 换成：a = "the cartoon woman on the LEFT (pink pajama shorts, white bunny slippers), facing RIGHT"；b = "the cartoon man on the RIGHT (navy blue shorts above the knee, black cat slippers), facing LEFT"。
**不要写 "bare legs"**：女生腿部局部重绘带这个词时被内容审核拒了（422 declined），去掉后通过。男生 PASSING 也被拒过一次，改成 "backward-stepping" + 写明哪只脚站地后通过。
