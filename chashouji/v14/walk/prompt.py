"""拖步每格的生图提示词 → <档>/prompts.txt。生图传两张图：[g<i>.png（拖鞋已贴好、腿区品红）, gait/<档>/base.png（原图，照它的腿画）]，不带蒙版。
带蒙版局部重绘只能给一张图，模型画出来的腿系统性偏细（腿宽 0.6~0.9 倍原图）；把原图当第二张参考才画得回原粗细。"""
import json, sys, os
W = os.path.dirname(os.path.abspath(__file__))       # v14/walk
name = sys.argv[1]
p = json.load(open(f'{W}/{name}/plan.json'))
A = name[0] == 'a'
WHO = ("woman (pink pajama shorts, white bunny slippers)" if A else "man (navy blue shorts, black cat slippers)")
SL = 'white bunny slippers' if A else 'black cat slippers'
TO, BACK = ('RIGHT', 'LEFT') if A else ('LEFT', 'RIGHT')
h = p['N'] // 2
out = []
for f in p['frames']:
    i = f['i']; ft = f['feet']
    back, front = ft['0'], ft['1']
    first = i < h
    u = (i if first else i - h) / h
    narrow = (u if first else 1 - u)          # 0 = 原图那么宽，1 = 收到最窄
    stance = (f"the slightly narrower stance of the two feet makes both knees bend a little more than in image 2" if narrow > 0.4 else
              f"the stance is almost as wide as in image 2")
    gap = 'closer together than' if narrow > 0.15 else 'almost as far apart as'
    if back['lift'] == 0 and front['lift'] == 0:
        legs = f"both slippers are flat on the floor and both legs bear weight; {stance}"
    else:
        mv, pl = ('front', 'back') if front['lift'] > 0 else ('back', 'front')
        side_mv = TO if mv == 'front' else BACK
        legs = (f"the {pl} slipper (on the {BACK if pl == 'back' else TO} side) is planted flat on the floor, its leg bears the weight; "
                f"the {mv} slipper (on the {side_mv} side) is lifted only a few centimeters off the floor and is sliding back toward the {BACK}: "
                f"that leg is dragging its foot backward low along the floor, heel slightly up; {stance}")
    pr = (f"Image 1 is the frame to complete, image 2 is the ORIGINAL drawing of the same {WHO}. "
          f"Output image 1 completed: keep everything in image 1 exactly — flat solid MAGENTA #FF00FF background, upper body, shorts, arms, phone, hair, the other person, "
          f"and BOTH {SL} exactly where they are in image 1 (same position, same size, do not add or remove slippers). "
          f"The slipper positions come ONLY from image 1 — they are {gap} in image 2, do not move them back to where they are in image 2; image 2 is only the reference for how the legs look. "
          f"Draw the two missing legs (the magenta gap between the shorts and the slippers): the {TO.lower()} leg goes into the {TO.lower()} slipper, the {BACK.lower()} leg goes into the {BACK.lower()} slipper — "
          f"the legs never cross, the front leg stays in front and the back leg stays behind. "
          f"Copy the legs of image 2: same thick full thighs and calves, same width at every height, same leg length, same knee shape, same skin color and outline; both legs equally thick. "
          f"Pose: {legs}. Walking BACKWARD toward the {BACK} with small shuffling steps while pulling, still facing the opponent. "
          f"Exactly two legs, no twisted or backward-bent knees. Flat 2D cel-shaded cartoon, thick black outlines, same as image 2. Background solid flat magenta #FF00FF, never black.")
    out.append(f"### {i:02d}\n{pr}\n")
open(f'{W}/{name}/prompts.txt', 'w').write('\n'.join(out))
