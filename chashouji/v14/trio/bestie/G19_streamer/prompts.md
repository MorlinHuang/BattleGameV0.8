# G19 网红主播（哥们美术代做，2026-09-30）—— 上方，坐无人机从左边飞进来，甩打赏小火箭（3D prop_rocket）

人和无人机**分开生**：无人机做成挂件层（web/assets/trio/G19_drone.webp，z −1，pivot = 机身顶面），每一帧同一张图、同一个位置，
对应第七轮 G15 船头"布景各帧逐像素相同"的要求。人一律画成"坐在看不见的座上"，屁股 + 大腿配准。

## raw/act_a0.png（idle / wind / throw / follow），参考 raw/ref_green.png（= ref/G19.png 铺绿幕），1024x1024 n2，绿幕（她一身粉紫，不能用品红）
外观逐项（粉紫长卷发、白色猫耳耳机带粉光圈、粉色短款拉链卫衣、白色超短牛仔裤带粉系带、白短袜、白粉厚底鞋）+ "the drone is REMOVED, sits in mid-air on an invisible seat"，朝右，手里只有一部手机。
问题：wind 举的是后侧手，throw / follow 甩的是前侧手，两只手对不上。备选 act_a0_alt.png（透明底，抠边有白毛）。

## raw/act_a1.png = act_a0 上蒙版只重绘 wind 格的上半身（inpaint/base_a.png + mask_a.png，头框锁住）
"FAR-side arm holds the smartphone beside her face … NEAR-side arm raised high above her head, bent backward, open empty hand"。
回来是透明底；头发缝里夹着绿点，铺回绿幕（act_a1g.png）按绿幕抠。备选 act_a1_alt.png（举的仍是后侧手，不用）。

## raw/act_b1.png（zoom / brake / wave / idle2），参考 act_a0.png，n2
前倾冲、头发往后拖 / 后仰急刹、两脚往前踢 / 挥手打招呼 / idle 同 act_a1 左上。透明底，同样铺绿幕 → act_b1g.png。备选 act_b1_alt.png。

## raw/drone.png：只画无人机（参考 ref_green.png，"girl completely removed"），1536x1024 n2，绿幕；part.py 缩到宽 260。备选 drone_alt.png。

## frames.json
ref idle，head [140,10,280,190]，fixed = 屁股 + 大腿 [120,300,280,400]，anchor 屁股坐点 [160,395]，size h 300，scale_by sheet。
残差 ≤ 1.01 px；wind"头 0.92"是举过头顶的手压进了头框，同一张条缩放 1.00。人 idle 剪影 2.53 万 × 0.9² ≈ 2.05 万（G11 2.06 万）。
进场 zoom / brake 不进 loose（loose 按脚底贴地面线，brake 两脚踢起来会把人整个往下拉）；按屁股配准，坐点不动。

## 命中
recipe 'star'。名单写"打中炸彩纸"，main.js RECIPE 里没有彩纸配方（记入 docs/待办.md）。
