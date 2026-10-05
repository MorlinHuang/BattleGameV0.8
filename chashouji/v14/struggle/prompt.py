"""挣扎帧重画的提示词（10-05 用户：「男生的腿仍然略有粗细不同，一点点畸形」「女生趴下的时候腿和男生一样」）。
旧 s1~s3 是拿 base 做蒙版局部重绘、只给一张图，模型画出来的腿粗细不一（腿宽 0.80~1.01 倍原图）、小腿鼓包、拖鞋换了款。
重画传两张图：[g<k>.png（struggle/guide.py：旧 s<k> 腿抹成品红、只留拖鞋落点）, base.png（腿的粗细、长短、肤色、拖鞋照它）]，不带蒙版 —— 同 walk/prompt.py 的道理。
用法 prompt.py <档> <k> → 打印提示词"""
import sys
name, k = sys.argv[1], int(sys.argv[2])
A = name[0] == 'a'                 # a 档女生赢、男生被拖；b 档反过来
WHO = "man (navy blue shorts, black cat slippers)" if A else "woman (pink pajama shorts, white bunny slippers)"
SL = 'black cat slippers' if A else 'white bunny slippers'
# 每档腿怎么接到拖鞋上（拖鞋落点就是姿势，这里只说规则）；第 3 个参数可以给这一格单写一句
RULE = {'K': "Kneeling: both knees stay on the floor where they are in image 2; each lower leg runs from its knee back to its slipper — "
             "a slipper higher than in image 2 means that lower leg is lifted off the floor, kicking.",
        'F': "Fallen forward: the thighs and knees stay low near the floor as in image 2; each lower leg runs to its slipper — "
             "a slipper up in the air means that knee is bent and the lower leg kicks up.",
        'L': "Lying on the belly: the thighs lie flat on the floor; a slipper up in the air means that knee is bent and the lower leg kicks up, "
             "a slipper on the floor means that leg lies straight along the floor."}[name[1]]
POSE_K = sys.argv[3] if len(sys.argv) > 3 else RULE
POSE = {'K': 'kneeling on the floor', 'F': 'fallen forward onto the floor', 'L': 'lying flat on the floor on the belly'}[name[1]]
print(f"Image 1 is the frame to complete, image 2 is the ORIGINAL drawing of the same scene. In image 1 the {WHO} who is {POSE} is missing both legs: "
      f"there is a magenta gap between the shorts and the two {SL}. Draw the two missing legs connecting the shorts to the slippers — each slipper stays EXACTLY where it is in image 1 "
      f"(same position, same angle, same size; do not move, add or remove slippers), and is worn on a foot; the slippers' design and face must be exactly the {SL} of image 2 (same face, same colors). {POSE_K} "
      f"The legs must look exactly like that person's legs in image 2: same thickness at every height along thigh, knee and calf, same leg length, "
      f"smooth even shape with no bulging muscles, no thin or pinched parts, both legs equally thick, same skin color, same thick black outline, same simple cel shading. "
      f"Keep everything else in image 1 exactly: flat solid MAGENTA #FF00FF background, the other person, shorts, upper body, arms, head, hair, phone. "
      f"Exactly two legs, no extra limbs, no twisted or backward-bent knees. Flat 2D cel-shaded cartoon, same style as image 2. Background solid flat magenta #FF00FF, never black.")
