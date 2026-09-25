# 步态帧生图 prompt（蒙版局部重绘）

每档：images=[gait/<档>/base.png]，mask=gait/<档>/mask.png，size=1536x1024，n=2，出 p2/p3/p4。
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
