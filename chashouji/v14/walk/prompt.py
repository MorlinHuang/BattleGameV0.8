import json, sys, os
W = os.path.dirname(os.path.abspath(__file__))       # v14/walk
name = sys.argv[1]
p = json.load(open(f'{W}/{name}/plan.json'))
A = name[0] == 'a'
WHO = ("the cartoon woman on the LEFT (pink pajama shorts, white bunny slippers), facing RIGHT" if A else
       "the cartoon man on the RIGHT (navy blue shorts above the knee, black cat slippers), facing LEFT")
SL = 'white bunny slippers' if A else 'black cat slippers'
TO, BACK = ('RIGHT', 'LEFT') if A else ('LEFT', 'RIGHT')
def side(x, other):
    return ('left' if x < other else 'right')
for f in p['frames']:
    i = f['i']; ft = f['feet']; a, b = ft['0'] if '0' in ft else ft[0], ft['1'] if '1' in ft else ft[1]
    near = p['near']
    st = a if a['lift'] == 0 else b
    sw = b if st is a else a
    nr = a if near == 0 else b
    nside = side(nr['x'], (b if nr is a else a)['x'])
    if sw['lift'] > 0: nside = 'lower one (flat on the floor)' if nr is st else 'raised one'
    else: nside += ' one' 
    u = (i % (p['N'] // 2)) / (p['N'] // 2)
    REL = (', still a little in front of the planted foot (toward the opponent)' if u < 0.4 else
           ', right beside the planted ankle (both slippers at nearly the same left-right position, one above the other)' if u < 0.6 else
           ', already behind the planted foot, about to land')
    if sw['lift'] == 0:
        legs = (f"both slippers are flat on the floor and both legs bear weight: the {BACK.lower()} slipper is behind her, the {TO.lower()} slipper is in front; wide stable backward-walking stance")
    else:
        legs = (f"the slipper that sits flat on the floor: that is the planted, weight-bearing foot, its leg firm; "
                f"the other slipper is raised about {int(sw['lift'])} pixels off the floor{REL}: that is the swinging foot, its knee bent, the lower leg angled so the heel leads toward the {BACK} — she is mid-step, stepping backward")
    pr = (f"Keep the ENTIRE image exactly as the reference, including the flat solid MAGENTA #FF00FF background, the upper body, the arms, the phone, the other person, "
          f"and BOTH {SL} exactly where they are (do not move, resize, redraw, duplicate or add slippers). "
          f"Inpaint ONLY the transparent masked area: draw the two legs of {WHO}, from the bottom of the shorts down into the two slippers, each leg connecting the hip to one slipper. "
          f"Pose: {legs}. The slipper that is the {nside} belongs to the NEAR leg (closer to the viewer, drawn overlapping the other leg). "
          f"Same leg length and thickness as the thighs at the top of the mask, natural knees pointing to the {TO} toward the opponent; she keeps facing the opponent and walks BACKWARD toward the {BACK} edge. Exactly two legs, no extra feet. "
          f"Style: flat 2D cel-shaded cartoon, thick black outlines, flat color fills, same as the reference. Background: solid flat magenta #FF00FF, no shadow, no floor, never black, never dark.")
    if not A: pr = pr.replace(' she ', ' he ').replace('she is', 'he is').replace('behind her', 'behind him')
    print(f"### {i:02d}\n{pr}\n")
