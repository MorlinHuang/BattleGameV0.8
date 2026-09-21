/* result.js —— 结算画面
 *
 * 这一屏不是"胜利弹窗"，是把这一局的**情绪**演完。
 *
 * 战斗画面里两个人从头到尾在拔一部手机，谁也没表态；赢的那一刻观众想看的
 * 不是"红方胜利"四个字，是**后果**——查到了会怎样、没查到又会怎样。所以结算
 * 全屏接管：一张 Q 版演出图铺满，判词压在上方墙面，赢家说的那句话用漫画
 * 气泡摆在旁边。血条到这里就撤掉了（顶上那两条属于对局中，结果已经写在
 * 画面里，再摆一遍是重复）。
 *
 * 两帧硬切循环是这一屏能不能活起来的关键。静图的"暴打"只是一个定格，观众
 * 盯三秒就腻；举起 / 砸下两帧、每帧 0.22 秒，就是一直在打。帧切换不做淡入，
 * 直接硬切 —— 项目里所有角色帧都是这么切的，模糊只会让动作发软。
 *
 * UI 这一套是被 Q 版画风逼出来的：圆角白板、粗黑描边、轻微倾斜、带投影，
 * 整体是"贴纸"。原先血条那套硬朗斜切金属条配到这张插画上会像两个软件拼在
 * 一起 —— 插画是圆的，UI 就得是圆的。
 *
 * 版式（960×1334，上下两头留给 UI，中间整块留给人）：
 *   0~210     判词贴纸 + 本局胜者角标；右上角常驻"下一局"倒计时
 *   214~390   台词气泡（在赢家头的**外侧**上方，压墙不压脸）
 *   390~1040  演出区，一个 UI 元素都不放
 *   1058~1300 三张数据贴纸卡 + 送礼榜横排
 * 这几个数不是排出来好看就行的：演出图在生成时就按"上五分之一留墙、下四分
 * 之一留地板"构的图，UI 只能待在那两头。拿一张随便构图的图进来，卡片会直接
 * 盖在两张脸上。
 */
'use strict';

const Result = (function () {
  const INK = '#1e1b24';
  const CN = 'system-ui,"PingFang SC","Microsoft YaHei",sans-serif';
  const NEXT = 8;              // 结算停留多久，到点自动开下一局

  /* 演出图。两套各两帧：a=查岗党胜 b=灭迹党胜。
     b 那套还没画，加载不到就退到纯色板 —— 缺素材不该让整屏白掉。 */
  const img = { a: [null, null], b: [null, null] };

  let pin = -1;                // ?overt=<秒> 把时间钉住，见 main.js

  async function load(v) {
    const q = v ? '?v=' + encodeURIComponent(v) : '';
    const one = (src) => new Promise((ok) => {
      const i = new Image(); i.onload = () => ok(i); i.onerror = () => ok(null);
      i.src = src + q;
    });
    const [a1, a2, b1, b2] = await Promise.all(
      ['win_a1', 'win_a2', 'win_b1', 'win_b2'].map(n => one(`assets/ui/${n}.webp`)));
    img.a = [a1, a2]; img.b = [b1, b2];
    return [a1, a2, b1, b2].filter(Boolean).length;
  }

  const ease = (v) => 1 - Math.pow(1 - (v < 0 ? 0 : v > 1 ? 1 : v), 3);
  // 弹出用的回弹：冲过 1 再落回来，贴纸"啪"地贴上去的那一下
  const pop = (v) => {
    if (v <= 0) return 0; if (v >= 1) return 1;
    return 1 + 2.7 * Math.pow(v - 1, 3) + 1.7 * Math.pow(v - 1, 2);
  };

  /* 贴纸字：黑壳 → 白圈 → 队色圈 → 白字，四层一起描。
     canvas 的 lineWidth 是**居中**的（一半描在字外面），所以这里的值是离线
     试版时那套 27/17/9 的两倍。 */
  function sticker(ctx, s, x, y, size, ring) {
    ctx.font = `900 ${size}px ${CN}`;
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
    ctx.lineJoin = 'round'; ctx.miterLimit = 2;
    for (const [lw, col] of [[54, INK], [34, '#fff'], [18, ring]]) {
      ctx.lineWidth = lw; ctx.strokeStyle = col; ctx.strokeText(s, x, y);
    }
    ctx.fillStyle = '#fff'; ctx.fillText(s, x, y);
  }

  function card(ctx, x, y, w, h, r, fill) {
    ctx.beginPath(); ctx.roundRect(x, y, w, h, r);
    ctx.save();
    ctx.shadowColor = 'rgba(0,0,0,.38)'; ctx.shadowBlur = 16; ctx.shadowOffsetY = 8;
    ctx.fillStyle = fill; ctx.fill();
    ctx.restore();
    ctx.lineWidth = 7; ctx.strokeStyle = INK; ctx.stroke();
  }

  // 爆炸框：偶数顶点在外、奇数收进去九成，得到一圈浅锯齿
  function boom(ctx, cx, cy, w, h, n) {
    ctx.beginPath();
    for (let i = 0; i < n; i++) {
      const a = i / n * Math.PI * 2, k = i % 2 ? 0.90 : 1;
      const px = cx + Math.cos(a) * w / 2 * k, py = cy + Math.sin(a) * h / 2 * k;
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    }
    ctx.closePath();
  }

  function draw(ctx) {
    const t = S.overT, A = S.winner > 0;
    const c = A ? GREEN : RED, ring = rgba(c, 1);
    const pair = A ? img.a : img.b;

    ctx.save();

    /* 0~0.18 白闪：底下还是战斗画面，这一下是"定格"的那声响。
       演出图在 0.18 硬切进来，不淡入。 */
    if (t < 0.18) {
      ctx.fillStyle = `rgba(255,255,255,${0.92 * (1 - t / 0.18)})`;
      ctx.fillRect(0, 0, W, H);
      ctx.restore(); return;
    }

    /* ── 演出图：两帧硬切循环 ──────────────────────────────
       节奏不是等间隔的：蓄力 0.45 秒、命中 0.18 秒。等频交替（0.22/0.22）
       读起来是机械闪烁，不是人在打 —— 抡东西本来就是举起来慢、砸下去快。
       这个节奏还顺带压住了两帧之间的人物位移：生成的第二帧里跪着的那位
       也跟着挪了几十像素，等频快切会把它放大成"人在左右跳"。 */
    const HOLD = 0.45, HIT = 0.18, CYC = HOLD + HIT;
    const ph = t < 1.6 ? 0 : (t - 1.6) % CYC;
    const hit = ph >= HOLD && pair[1];
    const im = (hit ? pair[1] : pair[0]) || pair[0];
    /* 命中那一下整幅往下震一次。震的只有演出图，UI 不跟着动 ——
       字跟着抖会让人读不下去，而画面抖一下正是"打中了"。 */
    const sh = hit ? Math.sin((ph - HOLD) / HIT * Math.PI) * 6 : 0;
    /* 画的时候四边各放出 8px 余量：震下去的那一瞬，顶边会露出底下那张还没
       被盖住的战斗画面。现在两边都是同一堵墙、颜色撞上了才看不出来，换个
       底图就会露馅。 */
    if (im) ctx.drawImage(im, -8, sh - 8, W + 16, H + 16);
    else {
      // 兜底：素材缺了也得把结果交代清楚，不能白屏
      ctx.fillStyle = '#1a1e26'; ctx.fillRect(0, 0, W, H);
      ctx.fillStyle = rgba(c, .10); ctx.fillRect(0, 0, W, H);
    }

    // 上下各压一层渐变，UI 才浮得起来。幅度压小，压重了画面发灰
    let g = ctx.createLinearGradient(0, 0, 0, 230);
    g.addColorStop(0, 'rgba(22,26,36,.23)'); g.addColorStop(1, 'rgba(22,26,36,0)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, 230);
    g = ctx.createLinearGradient(0, H - 270, 0, H);
    g.addColorStop(0, 'rgba(20,22,32,0)'); g.addColorStop(1, 'rgba(20,22,32,.41)');
    ctx.fillStyle = g; ctx.fillRect(0, H - 270, W, 270);

    // ── 判词贴纸：1.38 倍砸下来 ─────────────────────────────
    const k1 = ease((t - 0.35) / 0.5);
    if (k1 > 0) {
      const title = A ? '查岗党 胜' : S.winner < 0 ? '灭迹党 胜' : '平 局';
      ctx.save();
      ctx.globalAlpha = k1;
      ctx.translate(MID, 118); ctx.rotate(-3.2 * Math.PI / 180);
      ctx.scale(1 + 0.38 * (1 - k1), 1 + 0.38 * (1 - k1));
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,.45)'; ctx.shadowBlur = 22; ctx.shadowOffsetY = 11;
      sticker(ctx, title, 0, 0, 108, S.winner === 0 ? 'rgba(235,238,244,1)' : ring);
      ctx.restore();

      // "本局胜者"角标：斜压在判词左肩上
      ctx.font = `700 27px ${CN}`;
      const tw = ctx.measureText(title).width;   // 注意：这里量的是角标字体下的宽度
      ctx.restore();
      ctx.save();
      ctx.globalAlpha = k1;
      ctx.translate(MID - 158, 40); ctx.rotate(-3.2 * Math.PI / 180);
      card(ctx, -119, -30, 238, 60, 28, rgba(c, .96));
      ctx.font = `700 27px ${CN}`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = INK; ctx.fillText(S.winner === 0 ? '本局打平' : '本局胜者', 0, 1);
      ctx.restore();
    }

    // ── 右上角常驻：下一局倒计时 ────────────────────────────
    if (k1 > 0) {
      const left = Math.max(0, Math.ceil(NEXT - t));
      ctx.save(); ctx.globalAlpha = k1;
      card(ctx, W - 238, 26, 214, 56, 26, 'rgba(38,36,48,.96)');
      ctx.font = `700 24px ${CN}`;
      ctx.textAlign = 'left'; ctx.textBaseline = 'middle';
      const s5 = `下一局  ${left}`;
      const w5 = ctx.measureText(s5).width;
      const x5 = W - 131 - (w5 + 26) / 2;
      ctx.fillStyle = '#fff'; ctx.fillText(s5, x5, 55);
      // ▸ 在中文字体里是空码位，画成三角才不会出豆腐块
      const tx = x5 + w5 + 11;
      ctx.beginPath(); ctx.moveTo(tx, 44); ctx.lineTo(tx + 15, 55); ctx.lineTo(tx, 66);
      ctx.closePath(); ctx.fillStyle = '#fff'; ctx.fill();
      ctx.restore();
    }

    // ── 台词气泡：写后果，不写胜负 ──────────────────────────
    const k2 = pop((t - 0.75) / 0.45);
    if (k2 > 0.001) {
      const line = A ? '让你背着我乱聊' : S.winner < 0 ? '都说了是工作群' : '谁也没撒手';
      const bw = 448, bh = 136;
      const bx = (A ? 492 : 42) + bw / 2 + 40, by = 214 + bh / 2 + 40;
      ctx.save();
      ctx.translate(bx, by); ctx.scale(k2, k2); ctx.translate(-bx, -by);
      ctx.save();
      ctx.shadowColor = 'rgba(0,0,0,.40)'; ctx.shadowBlur = 20; ctx.shadowOffsetY = 10;
      /* 尾巴指向说话的人。A 案女生在左下，尾巴就朝左下 —— 但不能拉太长，
         拉长了会变成一大块白三角压在抱枕上（试过，很丑）。漫画里尾巴本来
         也不必够到嘴，方向对了观众就连得起来。 */
      const tl = A
        ? [[bx - bw * 0.36, by + bh * 0.38], [bx - bw * 0.46, by + bh + 52], [bx - bw * 0.14, by + bh * 0.46]]
        : [[bx + bw * 0.36, by + bh * 0.38], [bx + bw * 0.46, by + bh + 52], [bx + bw * 0.14, by + bh * 0.46]];
      ctx.beginPath(); ctx.moveTo(tl[0][0], tl[0][1]);
      ctx.lineTo(tl[1][0], tl[1][1]); ctx.lineTo(tl[2][0], tl[2][1]); ctx.closePath();
      ctx.fillStyle = '#fff'; ctx.fill();
      ctx.restore();
      ctx.lineWidth = 7; ctx.strokeStyle = INK; ctx.stroke();
      boom(ctx, bx, by, bw, bh, 36);
      ctx.fillStyle = '#fff'; ctx.fill();
      ctx.lineWidth = 7; ctx.strokeStyle = INK; ctx.stroke();
      ctx.font = `900 46px ${CN}`;
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = INK; ctx.fillText(line, bx, by + 2);
      ctx.restore();
    }

    // ── 底部：三张数据卡 + 送礼榜 ───────────────────────────
    const k3 = ease((t - 1.15) / 0.5);
    if (k3 > 0) {
      ctx.save(); ctx.globalAlpha = k3; ctx.translate(0, 30 * (1 - k3));
      const el = Math.max(0, NUM.MATCH - S.clock);
      const cells = [
        ['本局时长', `${el / 60 | 0}:${String(el % 60 | 0).padStart(2, '0')}`],
        ['礼物', `${S.giftA} : ${S.giftB}`],
        ['最终拉力', `${S.fA.toFixed(0)} : ${S.fB.toFixed(0)}`],
      ];
      const cw = 290, ch = 112, gap = 15, x0 = (W - (cw * 3 + gap * 2)) / 2;
      cells.forEach(([lab, val], i) => {
        const x = x0 + i * (cw + gap);
        card(ctx, x, 1058, cw, ch, 24, 'rgba(255,255,255,.98)');
        ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
        ctx.font = `700 22px ${CN}`; ctx.fillStyle = '#747a8a';
        ctx.fillText(lab, x + cw / 2, 1058 + 27);
        ctx.font = `900 40px ${CN}`; ctx.fillStyle = INK;
        ctx.fillText(val, x + cw / 2, 1058 + 74);
        // 卡底一道队色：把三张卡和赢家那边绑在一起
        ctx.beginPath(); ctx.roundRect(x + 16, 1058 + ch - 13, cw - 32, 5, 3);
        ctx.fillStyle = rgba(c, .88); ctx.fill();
      });

      /* 送礼榜横排。竖排三行在这个画幅里装不下（试过：第三行顶到画布底边，
         数据卡还压住了两个人的腿），横排是唯一塞得下三个人的排法。
         代价是昵称要按格宽截断 —— 直播昵称长短差得远，不截会把金额挤出格子。 */
      const rw = cw * 3 + gap * 2, ry = 1184;
      card(ctx, x0, ry, rw, 96, 26, 'rgba(255,255,255,.98)');
      ctx.font = `700 23px ${CN}`;
      const tl2 = '送礼榜', tw2 = ctx.measureText(tl2).width;
      card(ctx, x0 + 13, ry + 24, tw2 + 30, 48, 24, rgba(c, .96));
      ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
      ctx.fillStyle = INK; ctx.fillText(tl2, x0 + 13 + (tw2 + 30) / 2, ry + 49);

      const sx = x0 + 13 + tw2 + 42, gw = (rw - (sx - x0) - 14) / 3;
      if (S.board.length) {
        S.board.slice(0, 3).forEach((b, i) => {
          const gx = sx + gw * i, bc = b.side > 0 ? GREEN : RED;
          if (i) { ctx.fillStyle = 'rgba(0,0,0,.15)'; ctx.fillRect(gx - 7, ry + 28, 1.5, 40); }
          ctx.beginPath(); ctx.arc(gx + 19, ry + 49, 15, 0, 7);
          ctx.fillStyle = rgba(bc, .92); ctx.fill();
          ctx.lineWidth = 5; ctx.strokeStyle = INK; ctx.stroke();
          ctx.font = `700 19px ${CN}`; ctx.textAlign = 'center';
          ctx.fillStyle = INK; ctx.fillText(String(i + 1), gx + 19, ry + 50);

          const amt = '+' + b.amt.toFixed(0);
          ctx.font = `900 23px ${CN}`;
          const aw = ctx.measureText(amt).width;
          ctx.textAlign = 'right';
          ctx.fillStyle = rgba(bc.map(v => v * 0.72 | 0), 1);
          ctx.fillText(amt, gx + gw - 16, ry + 49);

          ctx.font = `700 22px ${CN}`; ctx.textAlign = 'left';
          const room = gw - 46 - aw - 18;
          let nm = b.name;
          while (nm.length > 1 && ctx.measureText(nm + '…').width > room) nm = nm.slice(0, -1);
          if (nm !== b.name) nm += '…';
          ctx.fillStyle = INK; ctx.fillText(nm, gx + 42, ry + 49);
        });
      } else {
        /* 没接直播就说没接。**不摆编出来的名字** —— 那种画面一旦发出去，
           所有人都会以为这个功能已经在跑了。 */
        ctx.font = `700 22px ${CN}`; ctx.textAlign = 'center'; ctx.fillStyle = '#868c9a';
        ctx.fillText('— 接入直播后显示前三名 —', sx + (rw - (sx - x0) - 14) / 2, ry + 49);
      }
      ctx.restore();
    }
    ctx.restore();
  }

  return {
    load, draw,
    get NEXT() { return NEXT; },
    setPin(v) { pin = v; },
    get pin() { return pin; },
  };
})();
