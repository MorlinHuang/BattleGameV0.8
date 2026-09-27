# 示意：真相女神放大+抬高+只转上身+金色外发光+光芒光环+大喷雾。只做构图示意，不是游戏代码。
import sys, math, random
from PIL import Image, ImageDraw, ImageFilter, ImageChops
random.seed(3)
S_, FX_, FY_, OUT = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
BG = sys.argv[5] if len(sys.argv) > 5 else '/tmp/t5/W_bg_00040.png'
FACE = tuple(map(float, sys.argv[6].split(','))) if len(sys.argv) > 6 else (575, 835)
bg = Image.open(BG).convert('RGBA')
up = Image.open('web/assets/world/truth1_up.webp').convert('RGBA'); lo = Image.open('web/assets/world/truth1_lo.webp').convert('RGBA')
foot, piv, muz = (156, 459), (136, 184), (522, 63)
s = S_; X, Y = FX_ - foot[0]*s, FY_ - foot[1]*s
P = (X+piv[0]*s, Y+piv[1]*s); M = (X+muz[0]*s, Y+muz[1]*s)
da = math.atan2(FACE[1]-P[1], FACE[0]-P[0]) - math.atan2(M[1]-P[1], M[0]-P[0])
person = Image.new('RGBA', bg.size)
person.alpha_composite(lo.resize((round(lo.width*s), round(lo.height*s)), Image.LANCZOS), (round(X), round(Y)))
u = Image.new('RGBA', bg.size); u.alpha_composite(up.resize((round(up.width*s), round(up.height*s)), Image.LANCZOS), (round(X), round(Y)))
person.alpha_composite(u.rotate(-math.degrees(da), center=P, resample=Image.BICUBIC))
c, sn = math.cos(da), math.sin(da); Mr = (P[0]+(M[0]-P[0])*c-(M[1]-P[1])*sn, P[1]+(M[0]-P[0])*sn+(M[1]-P[1])*c)
out = bg.copy(); al = person.split()[3]; bb = al.getbbox(); cx, cy = (bb[0]+bb[2])/2-30, bb[1]+(bb[3]-bb[1])*0.35
R = Image.new('RGBA', bg.size); g = ImageDraw.Draw(R)
for i in range(16):
    t = i/16*2*math.pi; w = 0.07
    g.polygon([(cx, cy), (cx+700*math.cos(t-w), cy+700*math.sin(t-w)), (cx+700*math.cos(t+w), cy+700*math.sin(t+w))], fill=(255, 225, 120, 80))
R = R.filter(ImageFilter.GaussianBlur(14)); mk = Image.new('L', bg.size, 0)
ImageDraw.Draw(mk).ellipse((cx-360, cy-360, cx+360, cy+360), fill=255); mk = mk.filter(ImageFilter.GaussianBlur(110))
R.putalpha(ImageChops.multiply(R.split()[3], mk)); out.alpha_composite(R)
for grow, blur, rgb in [(21, 26, (255, 170, 40)), (9, 10, (255, 225, 120)), (3, 3, (255, 252, 220))]:
    L = Image.new('RGBA', bg.size, rgb+(0,)); L.putalpha(al.filter(ImageFilter.MaxFilter(grow)).filter(ImageFilter.GaussianBlur(blur))); out.alpha_composite(L)
out.alpha_composite(person)
# 光环：头顶（上身转过之后，取剪影最高处附近）
ys = [y for y in range(bb[1], bb[1]+40) for x in range(bb[0], bb[2], 3) if al.getpixel((x, y)) > 128]
hx = [x for x in range(bb[0], bb[2]) if al.getpixel((x, bb[1]+25)) > 128]; hx = sum(hx)/len(hx) if hx else bb[0]+60; hy = bb[1]-6
H = Image.new('RGBA', bg.size); ImageDraw.Draw(H).ellipse((hx-60*s, hy-16*s, hx+60*s, hy+16*s), outline=(255, 230, 120, 255), width=8)
out.alpha_composite(H.filter(ImageFilter.GaussianBlur(6))); out.alpha_composite(H)
Sp = Image.new('RGBA', bg.size); g = ImageDraw.Draw(Sp)
dx, dy = FACE[0]-Mr[0], FACE[1]-Mr[1]; Ld = math.hypot(dx, dy); ux, uy = dx/Ld, dy/Ld; nx, ny = -uy, ux
for i in range(700):
    t = random.random()**0.8*1.3; sp = (18+t*170)*(random.random()*2-1)
    x = Mr[0]+ux*Ld*t+nx*sp; y = Mr[1]+uy*Ld*t+ny*sp; r = 14+t*55
    g.ellipse((x-r-5, y-r-5, x+r+5, y+r+5), fill=(28, 120, 46, 34)); g.ellipse((x-r, y-r, x+r, y+r), fill=(156, 238, 96, 64))
for i in range(50):
    t = random.random()*0.3; x = Mr[0]+ux*Ld*t; y = Mr[1]+uy*Ld*t; r = 10+t*60
    g.ellipse((x-r, y-r, x+r, y+r), fill=(240, 255, 210, 70))
out.alpha_composite(Sp); g = ImageDraw.Draw(out)
for r, w, col in [(170, 10, (28, 120, 46, 255)), (160, 5, (156, 238, 96, 255)), (235, 6, (255, 225, 120, 200))]:
    g.ellipse((FACE[0]-r, FACE[1]-r*0.75, FACE[0]+r, FACE[1]+r*0.75), outline=col, width=w)
out.convert('RGB').save(OUT)
print('s', s, 'upper-body turn', round(da, 2), 'rad; bbox', bb, 'muzzle', [round(v) for v in Mr], 'gap to face', round(Ld))
