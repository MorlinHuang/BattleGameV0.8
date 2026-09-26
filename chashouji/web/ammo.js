/* ammo.js —— 礼物弹幕：飞过去，碰到对方的人才算数
 *
 * 分两层，跟 fx.js 的"形态 vs 题材"是同一个分法：
 *   样式（volley / single / heavy）—— 三种，管发射节奏与体量
 *   物品（发卡 / 抱枕 / 手柄 …）—— 可以无限加，只是皮
 * 观众不需要认出飞过来的是什么，光看节奏就知道这一发有多重。加新礼物只往
 * main.js 的 GIFT 表里添一行，这个文件不用动；除非要加新物品的画法。
 *
 * 命中判定用的是 frontAt(y, from) —— 挨打那个人在弹幕高度上朝这边的轮廓（main.js 给）；
 * 这一行没人时返回 null，那一发就从旁边飞过去。对冲掉的那些不碰人，在 midAt()（手机那条
 * 中线）前互相撞掉。发射时高度压进 targetSpan(from)：对方趴下以后只剩贴地那一截。
 * 瞄部位的礼物（GIFT.aim）例外：碰撞点是 aimAt(g, key) 给的那个部位，不是外轮廓。
 * 发射高度的范围由 main.js 按人物站位传进来（init 的 band），这里不写死
 * 画面几何：人物的大小和站位换过不止一次，每次都是这几个数先对不上。
 *
 * 物品目前是代码画的：几何剪影 + 粗描边 + 高对比色。飞行物在画面上只有
 * 60~160px 而且高速移动，这个精度足够验证节奏 —— 而节奏是这个功能的全部。
 * 之后换成生图贴图，只改 ITEM 表里的函数体。
 */
'use strict';

const Ammo = (function () {
  const MAX = 48;
  const act = [], pool = [];
  const queue = [];          // 待发射：连珠的后续几颗、重投的预警期
  const warns = [];          // 预警箭头
  let frontAt = null, midAt = null, targetSpan = null, aimAt = null, onHit = null, onClash = null, W = 960;
  /* 发射高度带：top~bot 是弹幕会飞的高度（大致就是人物从头到膝盖），
     face 是两张脸所在的那一段 —— 常规火力要绕开它，见 launch。 */
  let band = { top: 380, bot: 900, face: [520, 610] };

  function init(o) {
    frontAt = o.frontAt; midAt = o.midAt || (() => frontAt(0, 1)); targetSpan = o.targetSpan || (() => null);
    aimAt = o.aimAt || (() => null);
    onHit = o.onHit; onClash = o.onClash || (() => {}); W = o.W || 960;
    if (o.band) band = o.band;
  }

  /* 独占窗口。档 4 落地后的这一段时间里，别的东西不许出现在屏幕上 ——
     这是最强的一种表现手段，而且不需要任何新的粒子技术：观众看到的是
     "全世界让开，只有这一下"。礼物级的排队补发，常规火力直接丢掉
     （它只是火力的表现，数值那边早就算过了，少画几发不影响战况）。 */
  let lock = 0;
  const pending = [];

  /* ---------- 物品画法 ---------- */

  /* 都在原点画，调用方已经 translate + rotate 过了，r 是半宽。
     每一件都是"填充 + 深色粗描边"：底图是明亮客厅，实体靠轮廓而不是靠亮度
     才看得见 —— 跟角色睡衣有线稿是同一个道理。 */
  const INK = 'rgb(52,40,36)';
  function ink(ctx, lw) { ctx.lineWidth = lw; ctx.strokeStyle = INK; ctx.stroke(); }

  /* 鸭嘴夹的外轮廓：上窄下宽的 ∧ 形整块，纵向 ±1.02r、下沿 ±0.96r。
     3D 那版是**两片**各自成形、中间留 0.16r 的缝，照搬过来会翻车：这里 r=22，
     缝只有 3.5 屏幕px，而矢量描边 2px 一画（内外各一半）缝就被填死，六十多
     像素上读出来是一整个粉方块。跟 3D 建模那边同一条约束 —— 间隙小于两倍
     线宽，两条描边就并成一条黑带。
     所以矢量兜底版换了个表达：外轮廓画成合拢的一整片，两片的咬合面改用一条
     **锯齿 INK 线**画出来。齿是这件东西的第一识别点，缝不是；缝被填死就认不
     出是夹子，而一条锯齿线在 62px 上仍然读得出"带齿的咬合面"。
     两条路不会同屏出现（有贴图就走贴图），所以这里按可读性定形，不逐点复刻。 */
  function clipBody(ctx, r) {
    ctx.moveTo(-0.60 * r, -0.71 * r);
    ctx.lineTo(0.60 * r, -0.71 * r);
    ctx.lineTo(0.96 * r, 1.02 * r);
    ctx.lineTo(-0.96 * r, 1.02 * r);
    ctx.closePath();
  }

  /* 一颗瓜子壳：尖头朝 +x、钝头朝 -x，长 1.6r 宽 0.78r。
     两头都画成尖的话读起来像叶子或者杏仁，钝的那头才是瓜子。 */
  /* 一根香蕉的弯月形：中心线是一段下凹的圆弧，两头收尖。长 ±r、最粗 0.34r。 */
  function bananaPath(ctx, r) {
    ctx.moveTo(-r, -0.10 * r);
    ctx.quadraticCurveTo(0, 0.78 * r, r, -0.22 * r);      // 外弧（下沿）
    ctx.quadraticCurveTo(0, 0.12 * r, -r, -0.10 * r);     // 内弧（上沿）
    ctx.closePath();
  }

  // 口红管身（到内管顶为止）：宽 0.72r、高 ±0.9r 的上下两段台阶，膏体另画
  function lipstickPath(ctx, r) {
    ctx.moveTo(-0.36 * r, 0.9 * r); ctx.lineTo(-0.36 * r, 0.02 * r); ctx.lineTo(-0.3 * r, 0.02 * r);
    ctx.lineTo(-0.3 * r, -0.38 * r); ctx.lineTo(0.3 * r, -0.38 * r); ctx.lineTo(0.3 * r, 0.02 * r);
    ctx.lineTo(0.36 * r, 0.02 * r); ctx.lineTo(0.36 * r, 0.9 * r); ctx.closePath();
  }

  function kernel(ctx, r) {
    ctx.moveTo(r * 0.80, 0);
    ctx.quadraticCurveTo(r * 0.25, r * 0.39, -r * 0.45, r * 0.34);
    ctx.quadraticCurveTo(-r * 0.86, r * 0.21, -r * 0.86, 0);
    ctx.quadraticCurveTo(-r * 0.86, -r * 0.21, -r * 0.45, -r * 0.34);
    ctx.quadraticCurveTo(r * 0.25, -r * 0.39, r * 0.80, 0);
  }

  /* 一撮瓜子怎么摆：一颗横躺打底，另外四颗按黄金角散着斜插在它上面，彼此
     压住但不平行。平行摆过 —— 两条轮廓并成一根黑杠，读成一片叶子。
     [dx, dy, 角度]，单位 r / 弧度。 */
  const SEEDLAY = [[0, 0, 0], [0.17, 0.11, 0.86], [-0.13, -0.15, 1.98],
                   [0.09, -0.19, 3.44], [-0.15, 0.17, 5.12]];

  const ITEM = {
    /* 发卡：带齿的鸭嘴夹，竖着飞。原先是"一根粉色小棒加一颗珠子" —— 那个形体
       在 3D 转盘里剥掉外轮廓之后内部一条描边都不剩（结构密度 0%），转起来就是
       一张打转的贴纸。换成鸭嘴夹是为了给它**内部结构**：两片之间有缝、内缘有齿、
       顶上压一颗铰点珠。这里是矢量兜底（?nosprite 或素材没加载出来时走这条），
       尺寸照 3D 那版归一，两条路上飞的得是同一件东西。 */
    hairpin(ctx, r) {
      ctx.beginPath(); clipBody(ctx, r);
      ctx.fillStyle = '#ff7aab'; ctx.fill(); ink(ctx, r * 0.085);
      // 咬合面：一条来回三趟的锯齿线，对应 3D 版每片内缘那三颗齿
      ctx.beginPath();
      ctx.moveTo(0, -0.71 * r);
      for (let i = 0; i < 6; i++) {
        ctx.lineTo((i % 2 ? -0.19 : 0.19) * r, (-0.71 + 1.73 * (i + 0.5) / 6) * r);
      }
      ctx.lineTo(0, 1.02 * r);
      ctx.lineWidth = r * 0.085; ctx.strokeStyle = INK;
      ctx.lineJoin = 'miter'; ctx.stroke(); ctx.lineJoin = 'round';
      ctx.beginPath(); ctx.arc(0, -r * 0.76, r * 0.26, 0, 6.2832);
      ctx.fillStyle = '#ffb8d4'; ctx.fill(); ink(ctx, r * 0.085);
    },

    // 口红（没有贴图时的矢量兜底）：淡红管身 + 金箍 + 斜切的深红膏体，竖着
    lipstick(ctx, r) {
      ctx.beginPath(); lipstickPath(ctx, r);
      ctx.fillStyle = '#ff9aa2'; ctx.fill(); ink(ctx, r * 0.085);
      ctx.beginPath(); ctx.moveTo(-0.22 * r, -0.38 * r); ctx.lineTo(-0.22 * r, -0.62 * r);
      ctx.lineTo(0.22 * r, -0.88 * r); ctx.lineTo(0.22 * r, -0.38 * r); ctx.closePath();
      ctx.fillStyle = '#e8364e'; ctx.fill(); ink(ctx, r * 0.085);
      ctx.fillStyle = '#f2c14e'; ctx.fillRect(-0.38 * r, 0.02 * r, 0.76 * r, 0.16 * r);
    },

    // 香蕉（没有贴图时的矢量兜底）：黄身 + 深色果柄与尖头
    banana(ctx, r) {
      ctx.beginPath(); bananaPath(ctx, r);
      ctx.fillStyle = '#ffd21e'; ctx.fill(); ink(ctx, r * 0.09);
      ctx.beginPath(); ctx.arc(-r * 0.98, -r * 0.12, r * 0.09, 0, 6.2832);
      ctx.fillStyle = '#5e6a1e'; ctx.fill();
      ctx.beginPath(); ctx.arc(r * 0.97, -r * 0.21, r * 0.07, 0, 6.2832);
      ctx.fillStyle = '#3a2616'; ctx.fill();
    },

    /* 瓜子：一撮五颗，不是一颗。同样是为了内部结构 —— 单颗水滴的结构密度是 0，
       五颗交叉叠着才有彼此遮挡的接缝可读。男方的连珠，嗑瓜子看戏顺手弹过去。 */
    seed(ctx, r) {
      for (const [dx, dy, a] of SEEDLAY) {
        ctx.save();
        ctx.translate(dx * r, dy * r); ctx.rotate(a);
        ctx.beginPath(); kernel(ctx, r * 0.62);
        ctx.fillStyle = '#6b5136'; ctx.fill(); ink(ctx, r * 0.09);
        ctx.beginPath();
        ctx.moveTo(r * 0.30, 0); ctx.lineTo(-r * 0.40, 0);
        ctx.lineWidth = r * 0.07; ctx.strokeStyle = '#ae9570'; ctx.stroke();
        ctx.restore();
      }
    },

    // 抱枕：圆角方 + 缝线 + 两点兔耳暗示，跟沙发上那只兔抱枕呼应
    pillow(ctx, r) {
      ctx.beginPath(); ctx.roundRect(-r, -r * 0.84, r * 2, r * 1.68, r * 0.4);
      ctx.fillStyle = '#fdf2f6'; ctx.fill(); ink(ctx, r * 0.12);
      ctx.beginPath(); ctx.roundRect(-r * 0.78, -r * 0.64, r * 1.56, r * 1.28, r * 0.3);
      ctx.lineWidth = r * 0.055; ctx.strokeStyle = 'rgba(255,160,195,.85)'; ctx.stroke();
      ctx.fillStyle = '#ffb3cd';
      for (const s of [-1, 1]) {
        ctx.beginPath(); ctx.ellipse(s * r * 0.26, -r * 0.16, r * 0.1, r * 0.26, 0, 0, 6.2832); ctx.fill();
      }
    },

    // 游戏手柄：深色机身 + 一个摇杆一个按键，小但好认
    gamepad(ctx, r) {
      ctx.beginPath(); ctx.roundRect(-r, -r * 0.48, r * 2, r * 0.96, r * 0.44);
      ctx.fillStyle = '#3d4450'; ctx.fill(); ink(ctx, r * 0.12);
      ctx.beginPath(); ctx.arc(-r * 0.46, 0, r * 0.22, 0, 6.2832);
      ctx.fillStyle = '#8fe3ff'; ctx.fill(); ink(ctx, r * 0.08);
      ctx.beginPath(); ctx.arc(r * 0.44, -r * 0.08, r * 0.16, 0, 6.2832);
      ctx.fillStyle = '#ff7a7a'; ctx.fill(); ink(ctx, r * 0.07);
    },

    /* 玫瑰花束（档 3）。剪影必须是**放射状**的 —— 它对面那件是奶茶杯（梯形），
       两件飞在半空时观众只看得到纯色轮廓，一个发散一个收拢才分得开。
       这也是它换掉棉被的原因：棉被 1:0.70 和外卖箱 1:0.72 在剪影层上是
       两个一模一样的大方块。 */
    bouquet(ctx, r) {
      // 包装纸：底下那个倒锥
      ctx.beginPath();
      ctx.moveTo(-r * 0.30, r * 0.20); ctx.lineTo(r * 0.30, r * 0.20);
      ctx.lineTo(r * 0.16, r * 0.95); ctx.lineTo(-r * 0.16, r * 0.95);
      ctx.closePath();
      ctx.fillStyle = '#f7e3cf'; ctx.fill(); ink(ctx, r * 0.09);
      // 叶子先铺一层，压在花底下
      ctx.fillStyle = '#5f8f57';
      for (const a of [-2.5, -0.65, 3.55, 1.75]) {
        ctx.save(); ctx.translate(Math.cos(a) * r * 0.62, Math.sin(a) * r * 0.62 - r * 0.18);
        ctx.rotate(a);
        ctx.beginPath(); ctx.ellipse(0, 0, r * 0.34, r * 0.13, 0, 0, 6.2832); ctx.fill();
        ctx.restore();
      }
      // 七朵花头按放射排开，这就是那个"发散"的轮廓
      const heads = [[0, -0.72], [-0.60, -0.42], [0.60, -0.42],
                     [-0.72, 0.10], [0.72, 0.10], [-0.28, -0.06], [0.30, -0.10]];
      for (let i = 0; i < heads.length; i++) {
        const hx = heads[i][0] * r, hy = heads[i][1] * r, hr = r * (i < 3 ? 0.32 : 0.27);
        ctx.beginPath(); ctx.arc(hx, hy, hr, 0, 6.2832);
        ctx.fillStyle = i % 3 === 1 ? '#ff5f86' : '#e63a62'; ctx.fill(); ink(ctx, r * 0.075);
        // 花心那一圈：没有它七个圆读成七颗球
        ctx.beginPath(); ctx.arc(hx, hy, hr * 0.44, 0, 6.2832);
        ctx.strokeStyle = 'rgba(255,196,214,.9)'; ctx.lineWidth = r * 0.05; ctx.stroke();
      }
    },

    /* 奶茶（档 3）。上宽下窄的杯子 + 一根斜插的吸管，轮廓收拢，跟对面的
       花束正好相反。珍珠不画在杯里 —— 飞行时那么小根本看不见，它们留到
       命中时才作为粒子出场。 */
    milktea(ctx, r) {
      ctx.beginPath();
      ctx.moveTo(-r * 0.56, -r * 0.86); ctx.lineTo(r * 0.56, -r * 0.86);
      ctx.lineTo(r * 0.40, r * 0.96); ctx.lineTo(-r * 0.40, r * 0.96);
      ctx.closePath();
      ctx.fillStyle = '#e8c9a0'; ctx.fill(); ink(ctx, r * 0.085);
      // 杯底那层珍珠：一条深色带子，比画一堆小圆更容易读
      ctx.save(); ctx.beginPath();
      ctx.moveTo(-r * 0.46, r * 0.36); ctx.lineTo(r * 0.46, r * 0.36);
      ctx.lineTo(r * 0.40, r * 0.96); ctx.lineTo(-r * 0.40, r * 0.96);
      ctx.closePath(); ctx.clip();
      ctx.fillStyle = '#4a3324'; ctx.fillRect(-r, r * 0.36, r * 2, r);
      ctx.restore();
      // 封膜
      ctx.beginPath(); ctx.roundRect(-r * 0.62, -r * 1.00, r * 1.24, r * 0.22, r * 0.07);
      ctx.fillStyle = '#fff4e4'; ctx.fill(); ink(ctx, r * 0.075);
      // 吸管：斜的，它是这件东西的识别点
      ctx.save(); ctx.translate(r * 0.10, -r * 0.30); ctx.rotate(-0.34);
      ctx.beginPath(); ctx.roundRect(-r * 0.09, -r * 0.95, r * 0.18, r * 1.5, r * 0.09);
      ctx.fillStyle = '#ff8fb8'; ctx.fill(); ink(ctx, r * 0.07);
      ctx.restore();
    },

    /* 求婚戒指盒（档 4）。开着盖飞过来 —— 合着的盒子只是个方块，跟档 2 的
       抱枕撞轮廓；掀开的盖子给了它一个别人没有的折角。
       它买的不是"更大的方块"，是命中那一刻绽开的东西。 */
    ringbox(ctx, r) {
      /* 掀开的盖子，向后仰。仰角和位移都要收着给：第一版 -0.42 配 -0.46
         的位移，盖子跟盒身之间开了一道缝，230px 宽的东西飞过去读成两个
         分开的粉方块，而不是一个开着的盒子。 */
      ctx.save(); ctx.translate(0, -r * 0.38); ctx.rotate(-0.30);
      ctx.beginPath(); ctx.roundRect(-r * 0.78, -r * 0.62, r * 1.56, r * 0.66, r * 0.1);
      ctx.fillStyle = '#c1416b'; ctx.fill(); ink(ctx, r * 0.075);
      ctx.beginPath(); ctx.roundRect(-r * 0.64, -r * 0.50, r * 1.28, r * 0.42, r * 0.08);
      ctx.fillStyle = '#ffe6ef'; ctx.fill();
      ctx.restore();
      // 盒身
      ctx.beginPath(); ctx.roundRect(-r * 0.80, -r * 0.10, r * 1.60, r * 0.86, r * 0.12);
      ctx.fillStyle = '#d4527d'; ctx.fill(); ink(ctx, r * 0.08);
      // 绒布槽
      ctx.beginPath(); ctx.ellipse(0, -r * 0.06, r * 0.50, r * 0.13, 0, 0, 6.2832);
      ctx.fillStyle = '#8f2d4f'; ctx.fill();
      /* 戒指：环 + 一颗钻，钻用菱形，圆的会读成又一颗珠子。
         尺寸比"真实比例"大一圈 —— 它是整件东西的识别点，按真比例画出来
         在飞行中只是一个小金点，观众读到的就只剩"一个粉盒子"了。 */
      ctx.beginPath(); ctx.arc(0, -r * 0.16, r * 0.30, 0, 6.2832);
      ctx.lineWidth = r * 0.13; ctx.strokeStyle = '#ffd35a'; ctx.stroke();
      ctx.lineWidth = r * 0.035; ctx.strokeStyle = 'rgba(122,82,20,.85)'; ctx.stroke();
      ctx.beginPath();
      ctx.moveTo(0, -r * 0.74); ctx.lineTo(r * 0.25, -r * 0.46);
      ctx.lineTo(0, -r * 0.20); ctx.lineTo(-r * 0.25, -r * 0.46);
      ctx.closePath();
      ctx.fillStyle = '#eaf7ff'; ctx.fill(); ink(ctx, r * 0.07);
    },

    /* 合照相框（档 4）。竖着的框 + 里面两个挨在一起的小人影。
       竖长比 1:1.3，跟戒指盒的 1:0.8 差 1.6 倍，剪影分得开。 */
    photo(ctx, r) {
      ctx.beginPath(); ctx.roundRect(-r * 0.68, -r * 0.90, r * 1.36, r * 1.80, r * 0.08);
      ctx.fillStyle = '#b8864f'; ctx.fill(); ink(ctx, r * 0.08);
      ctx.beginPath(); ctx.rect(-r * 0.52, -r * 0.74, r * 1.04, r * 1.48);
      ctx.fillStyle = '#fdf6ea'; ctx.fill(); ink(ctx, r * 0.05);
      // 照片里的两个人：肩线挨着，不画脸 —— 这个尺寸画脸只会糊成两个点
      ctx.fillStyle = '#7d93b5';
      for (const d of [-0.22, 0.22]) {
        ctx.beginPath(); ctx.arc(d * r, r * 0.02, r * 0.17, 0, 6.2832); ctx.fill();
        ctx.beginPath();
        ctx.ellipse(d * r, r * 0.52, r * 0.28, r * 0.30, 0, 3.1416, 6.2832);
        ctx.fill();
      }
      // 右上角一颗小爱心，把"这是合照"点破
      ctx.save(); ctx.translate(r * 0.34, -r * 0.46); ctx.scale(r * 0.013, r * 0.013);
      ctx.beginPath();
      ctx.moveTo(0, 11); ctx.bezierCurveTo(-13, 1, -7, -12, 0, -4);
      ctx.bezierCurveTo(7, -12, 13, 1, 0, 11); ctx.closePath();
      ctx.fillStyle = '#ff5f86'; ctx.fill();
      ctx.restore();
    },

    /* ↓ 以下两件是**备选池**，当前未启用（档 3 已换成花束/奶茶）。
       留着不是死代码：换回来只需改 main.js 的 ITEM_OF 一行。
       弃用原因见 docs/礼物设计.md 判据二 —— 两件剪影只差 1.03 倍。 */

    // 整条被子：最大的一件，格纹让它在翻滚时读得出体积
    quilt(ctx, r) {
      ctx.beginPath(); ctx.roundRect(-r, -r * 0.7, r * 2, r * 1.4, r * 0.18);
      ctx.fillStyle = '#ffe6ee'; ctx.fill(); ink(ctx, r * 0.085);
      ctx.strokeStyle = 'rgba(255,146,183,.8)'; ctx.lineWidth = r * 0.05;
      ctx.beginPath();
      for (const t of [-0.34, 0.34]) { ctx.moveTo(t * r * 2, -r * 0.7); ctx.lineTo(t * r * 2, r * 0.7); }
      for (const t of [-0.3, 0.3]) { ctx.moveTo(-r, t * r * 1.4); ctx.lineTo(r, t * r * 1.4); }
      ctx.stroke();
      // 翻出来的一角，不然大色块读成一块板子
      ctx.beginPath();
      ctx.moveTo(r, -r * 0.7); ctx.lineTo(r * 0.5, -r * 0.7); ctx.lineTo(r, -r * 0.2);
      ctx.closePath(); ctx.fillStyle = '#fff8fb'; ctx.fill(); ink(ctx, r * 0.07);
    },

    // 外卖箱：牛皮纸色 + 胶带十字，一眼是个箱子
    box(ctx, r) {
      ctx.beginPath(); ctx.roundRect(-r, -r * 0.72, r * 2, r * 1.44, r * 0.1);
      ctx.fillStyle = '#cf9760'; ctx.fill(); ink(ctx, r * 0.085);
      ctx.beginPath(); ctx.roundRect(-r, -r * 0.72, r * 2, r * 0.4, r * 0.1);
      ctx.fillStyle = '#b87f4b'; ctx.fill(); ink(ctx, r * 0.07);
      ctx.strokeStyle = 'rgba(246,238,222,.9)'; ctx.lineWidth = r * 0.13;
      ctx.beginPath();
      ctx.moveTo(0, -r * 0.72); ctx.lineTo(0, r * 0.72);
      ctx.moveTo(-r, r * 0.1); ctx.lineTo(r, r * 0.1);
      ctx.stroke();
    },
  };

  /* 外轮廓剪影 —— 残影专用。
     残影是速度残像，照着本体一笔一笔画满缝线、按键、格纹，既贵（四个残影
     就是四遍完整物品）又脏（细节在高速移动里糊成噪点）。它只需要形状。
     调用方负责 fill，这里只铺路径。 */
  const SILH = {
    // 发卡：∧ 形块加顶上的珠。残影是实心填充，锯齿接缝在这里画不出来，不画
    hairpin(ctx, r) {
      ctx.beginPath();
      clipBody(ctx, r);
      ctx.moveTo(r * 0.26, -r * 0.76);
      ctx.arc(0, -r * 0.76, r * 0.26, 0, 6.2832);
    },
    banana(ctx, r) { ctx.beginPath(); bananaPath(ctx, r); },
    lipstick(ctx, r) { ctx.beginPath(); lipstickPath(ctx, r); ctx.rect(-0.22 * r, -0.88 * r, 0.44 * r, 0.5 * r); },
    // 瓜子：五颗交叉的水滴，轮廓本身就是"一撮"的识别点
    seed(ctx, r) {
      ctx.beginPath();
      for (const [dx, dy, a] of SEEDLAY) {
        /* save/restore 夹着建路径是安全的：路径点在 addPath 那一刻就按当时的
           变换换算成用户空间坐标了，路径本身不属于 drawing state。 */
        ctx.save(); ctx.translate(dx * r, dy * r); ctx.rotate(a);
        kernel(ctx, r * 0.62);
        ctx.restore();
      }
    },
    pillow(ctx, r) { ctx.beginPath(); ctx.roundRect(-r, -r * 0.84, r * 2, r * 1.68, r * 0.4); },
    gamepad(ctx, r) { ctx.beginPath(); ctx.roundRect(-r, -r * 0.48, r * 2, r * 0.96, r * 0.44); },
    // 花束：外接的是七个花头，画成一圈交叠的圆 —— 放射轮廓就是它的识别点
    bouquet(ctx, r) {
      ctx.beginPath();
      ctx.moveTo(-r * 0.30, r * 0.20); ctx.lineTo(r * 0.30, r * 0.20);
      ctx.lineTo(r * 0.16, r * 0.95); ctx.lineTo(-r * 0.16, r * 0.95);
      ctx.closePath();
      for (const h of [[0, -0.72, 0.32], [-0.60, -0.42, 0.32], [0.60, -0.42, 0.32],
                       [-0.72, 0.10, 0.27], [0.72, 0.10, 0.27],
                       [-0.28, -0.06, 0.27], [0.30, -0.10, 0.27]]) {
        ctx.moveTo((h[0] + h[2]) * r, h[1] * r);
        ctx.arc(h[0] * r, h[1] * r, h[2] * r, 0, 6.2832);
      }
    },
    milktea(ctx, r) {
      ctx.beginPath();
      ctx.moveTo(-r * 0.56, -r * 0.86); ctx.lineTo(r * 0.56, -r * 0.86);
      ctx.lineTo(r * 0.40, r * 0.96); ctx.lineTo(-r * 0.40, r * 0.96);
      ctx.closePath();
      ctx.moveTo(-r * 0.62, -r * 1.00);
      ctx.rect(-r * 0.62, -r * 1.00, r * 1.24, r * 0.22);
    },
    ringbox(ctx, r) {
      ctx.beginPath();
      ctx.roundRect(-r * 0.80, -r * 0.10, r * 1.60, r * 0.86, r * 0.12);
      // 掀开的盖子单独补一块，斜的 —— 剪影上那个折角全靠它
      ctx.save(); ctx.translate(0, -r * 0.46); ctx.rotate(-0.42);
      ctx.roundRect(-r * 0.78, -r * 0.62, r * 1.56, r * 0.66, r * 0.1);
      ctx.restore();
    },
    photo(ctx, r) { ctx.beginPath(); ctx.roundRect(-r * 0.68, -r * 0.90, r * 1.36, r * 1.80, r * 0.08); },
    quilt(ctx, r) { ctx.beginPath(); ctx.roundRect(-r, -r * 0.7, r * 2, r * 1.4, r * 0.18); },
    box(ctx, r) { ctx.beginPath(); ctx.roundRect(-r, -r * 0.72, r * 2, r * 1.44, r * 0.1); },
  };

  /* 自发光的颜色。
     这里的"发光"不是加光。明亮客厅底图上 lighter 是加不上去的 —— 浅绿墙
     本来就接近饱和，任何颜色加上去都只是趋向白，红色叠浅绿直接变成纯白。
     所以走的是**色晕**：普通混合的半透明高饱和色，比本体大一圈、边缘柔化。
     它靠色相从背景里跳出来，跟粒子那套"发光的一律高饱和暖橙"是同一条规矩。

     取每件物品主色的高饱和版，顺带把阵营也读出来：查岗党偏粉紫，灭迹党偏
     琥珀与青。观众看一眼弹道的颜色就知道这一发是谁打的。 */
  const AURA = {
    hairpin: [255, 64, 156], lipstick: [255, 118, 128], pillow: [255, 92, 164], quilt: [255, 76, 148],
    seed: [255, 148, 48], banana: [255, 206, 40], gamepad: [64, 206, 255], box: [255, 136, 40],
    bouquet: [255, 48, 110], ringbox: [255, 186, 56],
    milktea: [255, 158, 72], photo: [255, 206, 140],
  };

  /* 色晕贴图一次性烘好。这台机器没有 GPU，每帧 createRadialGradient 是最贵的
     几件事之一 —— 跟 fx.js 里光斑的处理是同一个理由。六件物品六张，建完就
     不再动。 */
  /* 3D 渲出来的转盘序列。
     物品有两种画法：`ITEM` 里的矢量函数（画得出但转起来光影跟着一起转，物理上
     是错的），和这里的贴图序列（每个角度都是 Blender 渲的，光影各自正确）。
     有贴图就用贴图，没有就退回矢量 —— `?sim` 那条分支不加载任何素材，必须能退。

     `cell` 是单格边长，`n` 是转盘帧数，`scale` 补偿裁剪留白：图集是按**所有
     角度的并集**裁的，单帧物体填不满一格。

     转轴由建模侧的 `lean` 定（转轴从视线轴往屏幕横轴偏多少度），这里不管。
     一度以为"转法不对"是没有体积感的原因，量完才知道不是：真正决定体积感的是
     **剥掉外轮廓之后剪影里还剩多少结构**——转动时眼睛读到的是内部遮挡关系在变，
     外轮廓变化只说明形状变了。花束 46%、奶茶 25%、手柄 14%、抱枕 4%。
     见 `tools/3d/measure_volume.py`。

     `scale` 每次重渲都会变，必须照 `pack_atlas.py` 打印的那行填 —— 它跟着并集走，
     而并集跟着描边粗细走。描边现在按 `screen_r` 从"这件东西在屏幕上多大"倒推，
     八件统一 2.8px（见 tools/3d/common.py 的 _ink_thickness，那里有一个把描边
     按平方放大的坑）。 */
  const SPRITE = {
    bouquet: { src: 'assets/items/bouquet_atlas.webp', n: 36, cols: 6, cell: 272, scale: 1.35 },
    milktea: { src: 'assets/items/milktea_atlas.webp', n: 36, cols: 6, cell: 264, scale: 1.30 },
    ringbox: { src: 'assets/items/ringbox_atlas.webp', n: 36, cols: 6, cell: 336, scale: 1.61 },
    photo:   { src: 'assets/items/photo_atlas.webp',   n: 36, cols: 6, cell: 336, scale: 1.38 },
    hairpin: { src: 'assets/items/hairpin_atlas.webp', n: 36, cols: 6, cell: 138, scale: 1.42 },
    seed:    { src: 'assets/items/seed_atlas.webp',    n: 36, cols: 6, cell: 130, scale: 1.34 },
    banana:  { src: 'assets/items/banana_atlas.webp',  n: 36, cols: 6, cell: 160, scale: 1.09 },
    lipstick:{ src: 'assets/items/lipstick_atlas.webp', n: 36, cols: 6, cell: 160, scale: 1.13 },
    pillow:  { src: 'assets/items/pillow_atlas.webp',  n: 36, cols: 6, cell: 160, scale: 1.16 },
    gamepad: { src: 'assets/items/gamepad_atlas.webp', n: 36, cols: 6, cell: 160, scale: 1.06 },
  };

  /* 诊断开关。`bare` 只画物品本体，把色晕、拖尾、残影全关掉 —— 用来回答
     "看不出体积感，是转法不对还是被特效糊住了"这类问题。两个因素纠缠在
     一起时，单看成品图是分不出来的。 */
  let bare = false;
  function setBare(v) { bare = !!v; }

  function loadSprites(ver, off) {
    // ?nosprite=1 强制退回矢量画法 —— 用来和转盘版并排对比，两条路都要留着
    if (off) return Promise.resolve([]);
    const q = ver ? '?v=' + encodeURIComponent(ver) : '';
    return Promise.all(Object.keys(SPRITE).map((k) => new Promise((done) => {
      const sp = SPRITE[k], im = new Image();
      im.onload = () => {
        sp.img = im;
        /* 残影层要的是**单色剪影**，而贴图是彩色的。一次性烘一张染好色的
           副本，运行时直接 drawImage —— 跟 aura() 的做法是同一个理由：
           这台机器没有 GPU，每帧做合成是最贵的几件事之一。 */
        const c = document.createElement('canvas');
        c.width = im.width; c.height = im.height;
        const g = c.getContext('2d');
        g.drawImage(im, 0, 0);
        g.globalCompositeOperation = 'source-in';
        g.fillStyle = `rgb(${TAIL[k] || '52,40,36'})`;
        g.fillRect(0, 0, c.width, c.height);
        sp.silh = c;

        /* 边缘光用的剪影：同一张贴图，染成它自己的 AURA 色，**三分之一分辨率**。
           物品不是圆的，所以想要一圈贴着轮廓的薄光，光的形状只能取自物品自己 ——
           圆形渐变贴图怎么调都是个光斑。
           分辨率只取三分之一，两个理由：一是内存，全分辨率八件要多吃 66MB（原图
           加剪影已经占了两份），三分之一是 7MB；二是放大回去时双线性插值自带
           两三个像素的过渡，边就从"一道实色描边"变成了"一圈光"，不用再做模糊。
           逐格烘、格间留 2px 空边：整张缩小的话相邻格会互相采样进来 —— 打包时
           并集就是格边长，长轴正对镜头那几帧物品正好顶到格子边上，糊过去就是
           邻格的边渗进来一道杂色。 */
        const RS = 1 / 3, PAD = 2;
        const ce = Math.max(8, Math.round(sp.cell * RS)), step = ce + PAD * 2;
        const rows = Math.ceil(sp.n / sp.cols);
        const rc = document.createElement('canvas');
        rc.width = sp.cols * step; rc.height = rows * step;
        const rg = rc.getContext('2d');
        for (let i = 0; i < sp.n; i++) {
          const cx = i % sp.cols, cy = (i / sp.cols) | 0;
          rg.drawImage(im, cx * sp.cell, cy * sp.cell, sp.cell, sp.cell,
                       cx * step + PAD, cy * step + PAD, ce, ce);
        }
        rg.globalCompositeOperation = 'source-in';
        rg.fillStyle = `rgb(${(AURA[k] || [255, 140, 60]).join(',')})`;
        rg.fillRect(0, 0, rc.width, rc.height);
        sp.rim = rc; sp.rimCell = ce; sp.rimStep = step; sp.rimPad = PAD;

        done(true);
      };
      im.onerror = () => done(false);       // 缺素材不阻塞，退回矢量画法
      im.src = sp.src + q;
    })));
  }

  // 当前朝向对应转盘的哪一格
  function cellOf(sp, rot) {
    let k = Math.floor(rot / 6.2832 * sp.n) % sp.n;
    if (k < 0) k += sp.n;
    return k;
  }

  const auraCache = new Map();
  function aura(rgb) {
    const key = rgb[0] + ',' + rgb[1] + ',' + rgb[2];
    let c = auraCache.get(key);
    if (c) return c;
    const S = 128;
    c = document.createElement('canvas');
    c.width = c.height = S;
    const g = c.getContext('2d');
    /* 普通的中心浓、向外衰减的放射光。曾经把峰值挪到 0.63 做成环形，想让被
       本体盖住的那部分能量露出来 —— 方向错了：这张贴图是**圆**的，而物品不是。
       圆环贴不住轮廓，加浓之后露出来的不是"物体边上的一圈光"，是一个比物品
       大半圈的椭圆光斑，读起来就是物品底下压了一团影子。
       边缘光现在由 ⑤ 层负责，那一层的形状直接取自物品自己的剪影，贴得住。
       这张贴图退回它本来该干的活：**只摆在身后**当弹道余辉，不再画在本体下面，
       所以中心浓是对的，环形反而会让没有遮挡的余辉团读成烟圈。 */
    const rg = g.createRadialGradient(S / 2, S / 2, 0, S / 2, S / 2, S / 2);
    rg.addColorStop(0.00, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.80)`);
    rg.addColorStop(0.42, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.46)`);
    rg.addColorStop(0.74, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0.14)`);
    rg.addColorStop(1.00, `rgba(${rgb[0]},${rgb[1]},${rgb[2]},0)`);
    g.fillStyle = rg; g.fillRect(0, 0, S, S);
    auraCache.set(key, c);
    return c;
  }

  /* 拖尾带的颜色：每件物品自己主色的暗调，不是统一的黑。统一用深色的话，
     拖在浅粉抱枕后面读起来像一团影子或者污渍 —— 那是"另一个东西"，而拖尾
     应该是它自己甩出来的。 */
  const TAIL = {
    hairpin: '176,64,112', lipstick: '200,72,88', seed: '58,42,26', banana: '150,110,20', pillow: '196,116,150',
    gamepad: '38,46,58', quilt: '198,112,148', box: '126,82,48',
    bouquet: '150,42,72', milktea: '132,94,58',
    ringbox: '150,58,92', photo: '120,88,54',
  };

  /* ---------- 发射 ---------- */

  /* 重投给到 850 而不是更慢。直觉上"大件就该飞得慢"，但屏幕外到对抗线只有
     六百来像素，620 的时候光飞行就要一秒，加上预警一共一秒二 —— 中间那大半
     秒是匀速滑行，画面上什么也没发生，观众的注意力会飘走。分量感是靠体量、
     预警和落地那一下给的，不是靠拖时间。 */
  const SPEED = { volley: 1400, single: 900, heavy: 850 };
  /* 重投是唯一加速的。匀速的大件在屏幕上就是一路平移，中间大半秒什么也没
     发生 —— 拖沓的根子在匀速，不在速度值不够；单纯调快又会丢掉"看清它是
     什么"的那一段。加速两头都要：前段慢得认得出，后段砸得狠，总时长还短了
     三分之一。 */
  const ACC = { heavy: 900 };
  /* 每一发在基准速度上再抖一下。整批同速看着像传送带上排好的货，而连珠本来
     该读成"抓一把撒过去"—— 有的先到有的后到，命中的节奏才是碎的。
     重投抖得最少：它有预警，观众在等那一下，节奏不该飘。 */
  const JIT = { volley: 0.34, single: 0.26, heavy: 0.10 };

  /* g 是 main.js 的 GIFT 表里的一行。fixedY 只给诊断胶片用 —— 随机高度会让
     每次截出来的图不一样，没法比。 */
  function launch(g, fixedY, opt) {
    const o = opt || {};
    if (lock > 0 && !o.exec) {
      if (o.gift && pending.length < 6) pending.push([g, fixedY, o]);
      return;
    }
    const y0 = fixedY != null ? fixedY : band.top + Math.random() * (band.bot - band.top);
    if (o.exec) {
      /* 处决：预警拉长到半秒多，让全场先看见它要来；体积按 1.8 倍压过来。
         这是"倾倒式"演出的简化实现 —— 等美术到位再换成真正的倾泻，
         飞行逻辑一行都不用改。 */
      warns.push({ from: g.from, y: y0, t: 0.55, max: 0.55 });
      queue.push({ t: 0.55, g, y: y0, exec: true });
      return;
    }
    /* 常规火力：一发就是一发，不走连珠那一串。
       高度要避开两个人的脸（band.face）—— 火力弹幕是连绵不断的，糊在脸上的话
       整局都看不清表情，而表情是这个玩法仅有的两个可读信息之一。礼物弹幕是
       孤立事件，遮一下无妨；常态的那一路不行。 */
    if (o.one) {
      const yy = fixedY != null ? fixedY : (Math.random() < 0.45
        ? band.top + Math.random() * Math.max(0, band.face[0] - 14 - band.top)   // 脸以上
        : band.face[1] + 26 + Math.random() * Math.max(0, band.bot - band.face[1] - 26)); // 脸以下：手和腿
      queue.push({ t: 0, g, y: clampY(yy), clash: o.clash, free: true });
      return;
    }
    if (g.gap) {
      /* 一次礼物分几回扔、每回隔 gap 秒（香蕉 / 口红：三根、隔 0.5 秒）。跟连珠的差别是节奏：
         连珠 70ms 一颗读成"一把撒过去"，隔半秒一根读成"一根接一根地砸"。 */
      for (let i = 0; i < (g.n || 1); i++) queue.push({ t: i * g.gap, g, y: y0, fixed: fixedY != null });
    } else if (g.style === 'volley') {
      // 连珠：排成一串，间隔 70ms。每一颗单独判定、单独触发一次小命中，
      // 读起来是"哒哒哒"一串轻击而不是一下
      for (let i = 0; i < (g.n || 8); i++)
        queue.push({ t: i * 0.07, g, y: clampY(y0 + (Math.random() - 0.5) * 170) });
    } else if (g.style === 'heavy') {
      /* 重投先预警再发射。大礼物的价值一半在"全场都看见有人刷了大的"——
         冲进来之前得先让观众知道它要来，否则一个大件突然出现在画面里，
         观众只来得及看到它已经砸上了。 */
      warns.push({ from: g.from, y: y0, t: 0.25, max: 0.25 });
      queue.push({ t: 0.25, g, y: y0 });
    } else {
      queue.push({ t: 0, g, y: y0 });
    }
  }

  const clampY = (y) => y < band.top - 60 ? band.top - 60 : y > band.bot + 60 ? band.bot + 60 : y;
  const clamp01 = (v) => v < 0 ? 0 : v > 1 ? 1 : v;

  /* 轨迹环形缓冲的长度。原来是 8 帧，看着够，实际不够：被子 850px/s，八帧
     只往回退了 113 像素，而被子本身就有 156 像素宽 —— 拖尾比物体还短，整条
     全叠在本体底下，画了等于没画。 */
  const TRAIL = 16, TMASK = 15;

  /* 一发弹幕"拖多长"。
     取尺寸和速度里更大的那个：大件按自己的身长拖（否则拖尾埋在本体底下），
     快件按速度拖（一颗小发卡飞得再快，只按身长拖也读不出快）。两条各自都
     会在另一头失效，所以是 max 而不是二选一。 */
  const reachOf = (p) => Math.max(p.r * 2.6, Math.abs(p.vx) * 0.09);

  /* 沿轨迹往回找距离本体 dist 像素的那一点。
     残影和拖尾都按**距离**回溯，不按帧数 —— 按帧数的话同样是四个残影，
     发卡（1400px/s、半宽 22）能拖出四个身长，被子（850px/s、半宽 78）四帧
     只退 57 像素，全糊在本体上。眼睛读的是拖了多长，那是距离不是时间。 */
  function backAt(p, dist) {
    for (let k = 1; k < TRAIL; k++) {
      const idx = (p.hi + TRAIL - k) & TMASK;
      if (Math.abs(p.x - p.hx[idx]) >= dist) return idx;
    }
    return (p.hi + 1) & TMASK;
  }

  function fire(q) {
    /* 池满了就回收最老的那一发，而不是把新的丢掉。原来是直接 return ——
       观众刷了礼物，屏幕上却什么也没飞出来，这是连点时最糟糕的一种反馈。
       act 按发射顺序排，队头那一发飞得最久、离对抗线最近，让它提前退场的
       代价远小于让刚刷的这一件凭空消失。 */
    if (act.length >= MAX) pool.push(act.shift());
    const g = q.g, sp = SPEED[g.style] || 900;
    const p = pool.pop() || {};
    p.g = g; p.item = g.item; p.r = q.exec ? g.r * 1.8 : g.r;
    p.from = g.from;
    /* 高度压进对方身体此刻占的范围（上下各收 20，别擦着头顶/脚底）。在出手这一刻取，
       不在 launch 里取：重投有预警、连珠一串要排 0.5 秒，那期间人可能已经倒下了。 */
    const sp0 = targetSpan(g.from);
    p.y = sp0 ? Math.min(Math.max(q.y, sp0[0] + 20), sp0[1] - 20) : q.y;
    /* aim —— 瞄对方身上的一个部位（香蕉 'face' 女生的脸、口红 'hip' 男生的腰和大腿），**碰撞点也是
       那个部位**，不是外轮廓：香蕉从女生伸出来的手臂、头发边上穿过去，贴到脸上才爆。
       aimKey 是这一发在部位里挑的哪一点（0~1），飞行途中每帧按它重取 —— 人跪下 / 趴下 / 迈步，
       部位跟着挪，弹道一路微调高度追过去（见 update）。常规火力（free）不瞄，诊断胶片钉了高度的也不瞄。 */
    p.aimKey = null;
    if (g.aim && !q.free && !q.fixed) {
      const t = aimAt(g, p.aimKey = Math.random());
      if (t) p.y = t[1]; else p.aimKey = null;
    }
    p.exec = !!q.exec;
    p.clash = !!q.clash;
    // 对撞点落在自己这一侧一点，错开一些 —— 全撞在同一条线上会读成一堵墙
    p.clashOff = 20 + Math.random() * 90;
    p.x = g.from > 0 ? -g.r - 40 : W + g.r + 40;
    p.vx = g.from * sp * (1 + (Math.random() - 0.5) * 2 * (JIT[g.style] || 0.2));
    p.ax = ACC[g.style] || 0;
    /* 处决压过来的速度只有一半。它买的是"一段没人打断的时间"—— 嗖一下飞过去
       就把这段时间还回去了。慢，才有"全场都看着它过来"。 */
    if (p.exec) { p.vx *= 0.5; p.ax *= 0.35; }
    /* 起始朝向：从转盘第 0 格起步，只抖 ±10°。
       原来是 `Math.random() * 6.283` 满圈随机。飞行只有半秒、总共又只转半圈，
       起点落在哪儿就完全靠运气 —— 落在"手柄两个握把正好重叠成两团圆"那种
       相位上，观众这一整发就没看见过手柄长什么样。
       第 0 格是建模时的正面（八件都是），从正面起步、朝任一方向翻半圈，
       观众先认出这是什么，再看着它翻过去。抖那 ±10° 是为了齐射的八颗不至于
       整齐划一，读成复制粘贴。 */
    p.rot = (Math.random() - 0.5) * 0.35;
    /* 转速。矢量物品转的是一张平面图，快了只会晃眼；贴图物品转的是真的转盘，
       规矩是**飞行途中转半圈**（GIFT 表那里有完整推导）。
       原先写的是"必须转够一圈以上才看得出厚度"，那条是错的：按它给出来的
       14~15 每帧要转 14°，而转盘每格才 10° —— 每帧跳 1.4 格就进了走马灯区，
       读出来是闪不是转。半圈已经把可见面完整换过一遍，体积感全在里头。
       符号仍随机：顺着翻和倒着翻各用掉转盘的一半，36 格还是都用得上。 */
    /* 处决弹的转速跟着速度一起减半。这一句原先写在上面那行 exec 分支里
       （`p.vrot *= 0.5`），而 p.vrot 在这里才被赋值 —— 它改的是上一发留在
       对象池里的旧值，从来没生效过。处决弹速度减半、飞行时间翻倍，转速不
       跟着降就会在慢镜头里转足三圈，"全场都看着它过来"就变成了陀螺。 */
    p.vrot = (g.spin
      ? (Math.random() < 0.5 ? -1 : 1) * g.spin * (0.85 + Math.random() * 0.3)
      : (Math.random() - 0.5) * (g.style === 'volley' ? 26 : g.style === 'single' ? 13 : 4.5))
      * (p.exec ? 0.5 : 1);
    /* 轨迹环形缓冲：拖尾画的是这个东西**真正走过**的地方。原先那几条速度线
       是固定画在本体后方的，跟实际路径无关，所以飞得快飞得慢看上去一个样；
       记下真实轨迹之后，拖尾长度自己就跟速度挂上钩了。 */
    p.hx = p.hx || new Float64Array(TRAIL);
    p.hr = p.hr || new Float64Array(TRAIL);
    p.hx.fill(p.x); p.hr.fill(p.rot); p.hi = 0;
    p.x0 = p.x;                // 起点，用来算"飞到哪儿了"
    p.near = 0;                // 0 刚出场 → 1 贴上对抗线，色晕靠它烧起来
    act.push(p);
  }

  /* ---------- 推进 ---------- */

  function update(dt) {
    if (lock > 0 && (lock -= dt) <= 0) {
      lock = 0;
      while (pending.length) { const [g, y, o] = pending.shift(); launch(g, y, o); }
    }
    for (let i = queue.length - 1; i >= 0; i--) {
      const q = queue[i];
      q.t -= dt;
      if (q.t <= 0) { queue.splice(i, 1); fire(q); }
    }
    for (let i = warns.length - 1; i >= 0; i--) {
      warns[i].t -= dt;
      if (warns[i].t <= 0) warns.splice(i, 1);
    }
    for (let i = act.length - 1; i >= 0; i--) {
      const p = act[i];
      if (p.ax) p.vx += p.from * p.ax * dt;
      p.x += p.vx * dt;
      p.rot += p.vrot * dt;
      /* 重投在途中让画面一直轻轻发抖。每帧加的这一点点会被 0.86/帧 的衰减
         吃掉，稳态就在 1px 上下 —— 不是震动，是压迫感。 */
      if (p.g.style === 'heavy') Particles.addShake(0.15);

      p.hi = (p.hi + 1) & TMASK;
      p.hx[p.hi] = p.x; p.hr[p.hi] = p.rot;

      let fx;
      const t = p.aimKey != null && aimAt(p.g, p.aimKey);
      if (t) {
        /* 追部位：高度按指数趋近（与帧率无关），x 就是部位朝这边的那条边 */
        p.y += (t[1] - p.y) * (1 - Math.exp(-dt * 12));
        fx = t[0];
      } else fx = frontAt(p.y, p.from);
      const mx = midAt();
      /* 走完了全程的多少。色晕靠它在命中前一路烧起来 —— 观众在撞上之前就
         知道这一发要到了，而这正是弹幕能制造期待的唯一窗口。 */
      const span = (fx ?? mx) - p.x0;
      p.near = span === 0 ? 1 : clamp01((p.x - p.x0) / span);
      if (p.clash) {
        // 对冲掉的那些飞不到人身上，在中线前撞掉
        const cx = mx - p.from * p.clashOff;
        if (p.from > 0 ? p.x >= cx : p.x <= cx) {
          act.splice(i, 1); pool.push(p);
          onClash(p, cx);
          continue;
        }
      }
      const hit = fx != null && (p.from > 0 ? p.x >= fx : p.x <= fx);
      if (hit) {
        act.splice(i, 1); pool.push(p);
        /* 独占窗口从**命中那一刻**才开始。原来写在 launch 里，可处决要飞一秒半
           才落地 —— 等它真砸上的时候窗口早过期了，而飞行途中反倒把常规火力全
           丢光，画面空成一片。"全世界停下来看这一击"说的是这一击落地之后。 */
        if (p.exec) lock = 0.8;
        onHit(p, fx);
      } else if (p.x < -400 || p.x > W + 400) {
        // 没碰到人（这一行没人）就飞出画面，别让它永远飞下去
        act.splice(i, 1); pool.push(p);
      }
    }
  }

  /* ---------- 绘制 ---------- */

  function draw(ctx) {
    // 预警箭头：贴着发射方的屏幕边缘，闪两下
    for (const w of warns) {
      const k = w.t / w.max, blink = 0.5 + Math.abs(Math.sin(k * 18)) * 0.5;
      const x = w.from > 0 ? 58 : W - 58, d = w.from;
      const col = w.from > 0 ? 'rgb(126,217,87)' : 'rgb(255,72,72)';
      ctx.save();
      ctx.globalAlpha = blink;
      ctx.translate(x, w.y);
      // 越接近发射越大，读起来是"它正在逼近"
      ctx.scale(d * (1.1 + (1 - k) * 0.7), 1.1 + (1 - k) * 0.7);
      // 三重箭头，越靠后越淡：一个静止的三角读不出方向，一串才读得出"来了"
      for (let j = 0; j < 3; j++) {
        ctx.globalAlpha = blink * (1 - j * 0.3);
        ctx.beginPath();
        const ox = -j * 26;
        ctx.moveTo(ox + 26, 0); ctx.lineTo(ox - 12, -25); ctx.lineTo(ox - 12, 25);
        ctx.closePath();
        ctx.fillStyle = col; ctx.fill();
        ctx.lineWidth = 4.5; ctx.strokeStyle = 'rgba(20,16,22,.8)'; ctx.stroke();
      }
      ctx.restore();
    }

    for (let i = 0; i < act.length; i++) {
      const p = act[i];
      const au = AURA[p.item] || [255, 140, 60];
      const auStr = `rgb(${au[0]},${au[1]},${au[2]})`;
      const tex = aura(au);
      /* 这一发拖多长。色晕、拖尾、残影全按它摊开，所以三层永远是对齐的 ——
         分别写死各自的长度，快件和大件总有一头对不上。 */
      const reach = reachOf(p);
      const tail = p.hx[backAt(p, reach)];

      /* ① 弹道余辉：沿真实轨迹在**身后**摆两团，越靠后越小越淡。
         光要铺满整条路径 —— 弹道本身是暗的话，读出来是"一个发光的东西在
         移动"，而不是"它带着一道光在走"。
         身后两团，不含本体那一团。曾经有第三团压在本体正下方，半宽 1.55r，
         而本体轮廓横向就在 1.0r —— 于是每颗弹幕底下都垫着一圈比它大半圈的
         椭圆光斑。那东西贴不住轮廓（本体不是圆的），读起来是影子不是光。
         本体的边缘光归 ⑤ 层，那一层的形状取自物品剪影。这两团只管余辉，
         所以也收小降浓了（原来 1.55r×1.18r / gk 0.34~0.74）：余辉要的是
         "刚才有个亮东西从这儿过去了"，不是一路铺开的雾。
         越接近对抗线越浓：命中前的最后一段自己会烧起来。 */
      if (!bare) {
        ctx.save();
        const gk = 0.11 + p.near * 0.17;
        for (let k = 2; k >= 1; k--) {
          const idx = backAt(p, reach * k * 0.33);
          const f = 1 - k * 0.19;
          ctx.globalAlpha = gk * f * f;
          const gw = p.r * 1.02 * f, gh = p.r * 0.78 * f;
          ctx.drawImage(tex, p.hx[idx] - gw, p.y - gh, gw * 2, gh * 2);
        }
        ctx.restore();

        /* ② 拖尾带：从轨迹上 reach 那么远的一点收拢到本体。用暗调而不是亮色
           —— 明亮客厅底图上浅色线几乎看不见，跟粒子配色是同一条规矩：靠轮廓
           不靠亮度。长度是这一发**实际飞过**的距离，所以速度抖动一上来就看得
           出谁快谁慢。 */
        ctx.save();
        ctx.globalAlpha = 0.30;
        ctx.fillStyle = `rgb(${TAIL[p.item] || '52,40,36'})`;
        ctx.beginPath();
        ctx.moveTo(tail, p.y - p.r * 0.06);
        ctx.lineTo(p.x, p.y - p.r * 0.5);
        ctx.lineTo(p.x, p.y + p.r * 0.5);
        ctx.lineTo(tail, p.y + p.r * 0.06);
        ctx.closePath();
        ctx.fill();

        /* ③ 弹道亮芯：压在暗拖尾中间的一条细楔子。两条都要 —— 只有暗的读成
           一道划痕，只有亮的在浅底图上又浮不起来；暗的给实体感，亮的给能量感。 */
        ctx.globalAlpha = 0.48;
        ctx.fillStyle = auStr;
        ctx.beginPath();
        ctx.moveTo(tail, p.y);
        ctx.lineTo(p.x, p.y - p.r * 0.26);
        ctx.lineTo(p.x, p.y + p.r * 0.26);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      }

      /* ④ 残影：在它身后 reach 的四分之一、二分之一…处，把**外轮廓**再画
         一遍，越远越淡越小。只画轮廓不画内部细节 —— 缝线、按键、格纹在高速
         移动里糊成噪点，而且四个残影就是四遍完整物品，那是这个文件里最贵的
         一笔开销。

         用拖尾那个暗调，不用色晕色。残影是**物体的形状**，跟色晕、亮芯不是
         一回事 —— 三层全用同一个高饱和色的话，它们会融成一条实色带，形状
         就没了。发光的靠色相，实体的靠轮廓，这条规矩在这里同样成立。

         间距按距离均分，所以残影之间永远接得上：间距大于物体宽度的话读出来
         是"一串独立的小东西"，而不是"一个东西拖出来的影"。 */
      const sp = SPRITE[p.item];
      const useSp = sp && sp.img;

      if (!bare) {
        ctx.save();
        ctx.fillStyle = `rgb(${TAIL[p.item] || '52,40,36'})`;
        const silh = SILH[p.item];
        /* 残影数量和浓度分两套。矢量物品的 SILH 是**刻意简化过的**轮廓（花束就是
           七个圆），四个叠起来仍读作"影子"；贴图剪影带着全部细节（每片花瓣、
           叶子、包装纸），同样画四个、同样的浓度，糊出来是一大团暗红，比本体
           还抢眼，读成"另一个物体"而不是它的轨迹。
           贴图本身转盘就带足了运动信息，两个淡影够了。 */
        const k0 = useSp ? 2 : 4, ka = useSp ? 0.5 : 1;
        for (let k = k0; k >= 1; k--) {
          const idx = backAt(p, reach * k / k0);
          ctx.globalAlpha = (0.40 - k * 0.068) * ka;
          ctx.save();
          ctx.translate(p.hx[idx], p.y);
          const sc = 1 - k * 0.05;
          if (useSp) {
            /* 残影取**那一刻的朝向**对应的格子，不是当前朝向 —— 用当前朝向的话
               四个残影会是同一个姿势，读成"复制粘贴"而不是"它飞过来的轨迹"。
               这跟 hr[] 记录历史旋转角是同一个用意。 */
            const c = cellOf(sp, p.hr[idx]), e = sp.cell;
            const d = p.r * sp.scale * 2 * sc;
            ctx.drawImage(sp.silh, (c % sp.cols) * e, ((c / sp.cols) | 0) * e, e, e,
                          -d / 2, -d / 2, d, d);
          } else {
            ctx.rotate(p.hr[idx]);
            ctx.scale(sc, sc);
            silh(ctx, p.r);
            ctx.fill();
          }
          ctx.restore();
        }
        ctx.restore();
      }

      ctx.save();
      ctx.translate(p.x, p.y);

      /* ⑤ 边缘光：物品自己的剪影，染成 AURA 色，向外撑出几个像素，垫在本体
         正下方 —— 露出来的就是紧贴轮廓的一圈薄光。
         这一层是"自发光"的全部来源。之前那版靠圆形色晕贴图去做，怎么调都不对：
         圆的东西贴不住方的、扁的、带把手的轮廓，调淡了看不见，调浓了就是物品
         底下压了一团光斑。形状对了之后，浓度反而可以放心给足。
         撑出的量按**屏幕像素**算，不按半径比例：光边的宽度是个绝对观感，小件
         按比例算会细到看不见。整格放大 rim*2.8，物品轮廓在格内归一化半径 0.645
         （横向）、0.847（竖向），所以实际外扩是 0.9~1.2 个 rim —— 两个方向略有
         厚薄差，比圆形贴图那种 1.55 倍的错位小一个量级。
         贴图本体自带 2.8px 深色描边，这圈亮光落在描边**外侧**，深边夹在中间，
         正好是轮廓光该有的读法：物体是实的，边上挂着光。 */
      if (!bare) {
        ctx.globalAlpha = 0.30 + p.near * 0.24;
        /* 厚度：小件 2px、最大的花束 3px 出头，再算上贴图放大的柔边，观众看到
           的是 3~5px 的一道光。给得再宽一点就不是轮廓光了 —— 光一旦厚到能盖住
           物品自己的描边，读出来就是物品底下垫了个发光的影子。
           嫌淡/嫌浓就动这两个数：rim 是宽度（像素），上面那行的 alpha 是浓度。
           两个都别超过原来那版圆形色晕的量级 —— 那一版就是浓度堆上去之后，
           因为形状不对而读成了光斑。 */
        const rim = 1.5 + p.r * 0.020;
        if (useSp) {
          const c = cellOf(sp, p.rot), q = sp.rimStep, e = sp.rimCell;
          const dd = p.r * sp.scale * 2 + rim * 2.8;
          ctx.drawImage(sp.rim, (c % sp.cols) * q + sp.rimPad, ((c / sp.cols) | 0) * q + sp.rimPad,
                        e, e, -dd / 2, -dd / 2, dd, dd);
        } else {
          /* 矢量兜底：SILH 的轮廓半径就是 r，直接放大 1+rim/r。这条路没有贴图
             那种插值柔边，边会硬一点 —— 它本来就是素材没加载出来时的备胎。 */
          ctx.save();
          ctx.rotate(p.rot);
          const kr = 1 + rim / p.r;
          ctx.scale(kr, kr);
          ctx.fillStyle = auStr;
          SILH[p.item](ctx, p.r);
          ctx.fill();
          ctx.restore();
        }
        ctx.globalAlpha = 1;
      }

      if (useSp) {
        /* 贴图本体：**不转 canvas**。转盘序列里每一格自己就是那个角度渲好的，
           再叠一次 2D 旋转就成了"又翻又转"，而且光影会跟着 canvas 一起转，
           那正是换 3D 要解决的问题。 */
        const c = cellOf(sp, p.rot), e = sp.cell;
        const d = p.r * sp.scale * 2;
        ctx.drawImage(sp.img, (c % sp.cols) * e, ((c / sp.cols) | 0) * e, e, e,
                      -d / 2, -d / 2, d, d);
      } else {
        ctx.rotate(p.rot);
        ctx.lineJoin = 'round';
        ITEM[p.item](ctx, p.r);
      }
      ctx.restore();
    }
  }

  function clear() {
    while (act.length) pool.push(act.pop());
    queue.length = 0; warns.length = 0; pending.length = 0; lock = 0;
  }

  return { init, launch, update, draw, clear, loadSprites, setBare, ITEM, count: () => act.length + queue.length };
})();
