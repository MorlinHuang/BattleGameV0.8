/* 引擎写法测通用的临时数据（docs/三人组角色规范.md 第十节）。**不进正式页面**：kinds_test/serve.sh 在桌面搭一个测试页，
 * 页面文件全部符号链接到正式 web/，只多加载这一份，把两边的 cast / groups 换成下面这几个测试角色。
 * 素材借用现成三个样板的图集（B5 截拳道、B21 樱木、G11 格格），只为测进场 / 出手的写法本身；每个测试角色单独一组，?buddy= / ?bestie= 按组号召。 */
'use strict';
(() => {
  const b5 = TRIO_BUDDY.cast.B5, b21 = TRIO_BUDDY.cast.B21, b22 = TRIO_BUDDY.cast.B22, b27 = TRIO_BUDDY.cast.B27, g11 = TRIO_BESTIE.cast.G11;
  const { ropes, swing, enter: _e1, exit: _x1, parts: _p1, ...g } = g11;      // 格格去掉秋千，只借她的帧
  const { enter: _e2, exit: _x2, ...b } = b5;
  TRIO_BUDDY.cast = {
    /* 哥1 骑 / 滑进来 + 抽打（双节棍当链子甩：细链 + 末端一截黑棍） */
    T1: { ...b, enter: { kind: 'ride', tilt: 0.1, seq: [['walk2', 9]] }, exit: { frame: 'walk2' },
          atk: { kind: 'whip', seq: [['wind', 0.3], ['hitA', 0.45, 'fire'], ['taunt', 0.4]], from: [120, 104], phases: [0.12, 0.08, 0.22],
                 whip: { w: 3, taper: 1, amp: 18, waves: 1.5, hz: 4, color: '#c8c8d0', edge: 'rgba(40,40,50,.9)', tip: [58, 11, '#1b1b1b'] }, gap: [0.5, 0.8] } },
    /* 哥2 原地闪现 + 帧序列的伸缩拳（拳头从 hitA 那一格抠） */
    T2: { ...b, enter: { kind: 'appear', fx: 'flash', color: [255, 220, 120], seq: [['taunt', 0.4], ['idle', 9]] }, exit: { frame: 'idle' },
          atk: { kind: 'punch', seq: [['wind', 0.3], ['hitA', 0.55, 'fire'], ['taunt', 0.4]], fist: [128, 86, 172, 124], fistC: [150, 104], wrist: [182, 106],
                 armW: 15, skin: '#f7d24a', skinShade: 'rgba(170,120,0,.5)', skinEdge: '#3a2a00', fistZ: 1.3, phases: [0.14, 0.1, 0.28], gap: [0.5, 0.8] } },
    /* 哥3 跳落（从右边画外一个抛物线跳进来、砸地压扁）+ 丢东西冻住 */
    T3: { ...b21, enter: { kind: 'leap', h: 160, air: 0.4, sq: 0.12, seq: [['dive', 0.4], ['flop', 0.12, 'land'], ['slide', 0.2], ['idle', 9]] },
          atk: { ...b21.atk, onHit: 'freeze' } },
    /* 哥4 B22 蓄力球跟着蓄力帧的手：只比正式数据多一个 hold.wind（wind 帧双手合在腰侧那一点） */
    T8: { ...b22, atk: { ...b22.atk, hold: { ...b22.atk.hold, wind: [216, 160] } } },
    /* 哥5 3D 道具走图集只看 atlas、不看 item：B27 的牛丸把 item 写成真名 */
    T9: { ...b27, atk: { ...b27.atk, item: 'meatball' } },
    /* 哥6 走路一帧一步（stride = walk1 接地帧两脚距离，格内像素） */
    T10: { ...b5, enter: { ...b5.enter, stride: 190 } },
    B5: b5,                                               // 原数据（没写 stride）单独一组：量走路钉脚不被同组别人挡
    /* 哥7 / 哥8 / 哥9 后排出手从男生头顶翻过去：丢东西带线（借樱木的 3D 篮球）、喷、连打。
       出手点按规范写在举过头顶的那只手上（B5 wind 帧举棍的拳头 [270, 25]）—— 路只管中间那段，出发点得美术画高 */
    T11: { ...b5, atk: { ...b21.atk, seq: [['wind', 0.3], ['hitA', 0.3, 'fire'], ['taunt', 0.4]], hold: {}, from: [270, 25], tether: { w: 2.5, color: '#6a4b2a' }, onHit: null, gap: [0.5, 0.8] } },
    T13: { ...b5, atk: { ...b5.atk, from: [270, 25] } },
    T12: { ...b5, atk: { kind: 'spray', seq: [['wind', 0.3], ['hitA', 0.7, 'fire'], ['taunt', 0.4]], from: [270, 25], spray: { dur: 0.6, rate: 90, T: 0.3, tick: 0.15, color: [120, 200, 255], r: 18, spread: 0.14 }, gap: [0.5, 0.8] } },
  };
  TRIO_BUDDY.ground = {};
  TRIO_BUDDY.groups = [{ name: '骑+抽打', ground: 'T1' }, { name: '闪现+伸缩拳', ground: 'T2' }, { name: '跳落+冻住', floor: 'T3' },
                       { name: '蓄力球在手上', floor: 'T8' }, { name: '图集不认 item', floor: 'T9' },
                       { name: '走路钉脚', ground: 'T10' }, { name: '走路钉脚（原数据）', ground: 'B5' }, { name: '后排丢+带线', ground: 'T11' }, { name: '后排喷', ground: 'T12' }, { name: '后排连打', ground: 'T13' }];

  const hold = g11.atk.hold, fire4 = (d) => [['raise', 0.12], ['wind', 0.22], ['throw', d, 'fire'], ['follow', 0.3]];
  TRIO_BESTIE.cast = {
    /* 闺1 飞下（从左上画外减速飘到位）+ 喷雾 */
    T4: { ...g, enter: { kind: 'fly', tilt: 0.15, seq: [['tuck', 0.5], ['idle', 9]] }, exit: { frame: 'tuck' },
          atk: { kind: 'spray', seq: fire4(0.7), from: [277, 38], spray: { dur: 0.6, rate: 90, T: 0.3, tick: 0.15, color: [255, 120, 190], r: 18, spread: 0.14 }, gap: [0.5, 0.8] } },
    /* 闺2 倒挂垂下（顺着一根丝掉下来蹦两下）+ 斩痕 */
    T5: { ...g, enter: { kind: 'drop', len: 700, line: [128, 60], seq: [['tuck', 0.45], ['idle', 9]] }, exit: { frame: 'tuck' },
          atk: { kind: 'slash', seq: fire4(0.3), slash: { n: 3, gap: 0.08, len: 220, w: 18, life: 0.5, color: [150, 220, 255], ang: -0.5, spread: 0.3 }, gap: [0.5, 0.8] } },
    /* 闺3 从一条线后面升上来（烟）+ 抽打（红绸） */
    T6: { ...g, enter: { kind: 'appear', rise: 360, fx: 'smoke', color: [205, 195, 235], seq: [['kick', 0.5], ['idle', 9]] }, exit: { frame: 'tuck' },
          atk: { kind: 'whip', seq: fire4(0.44), from: [277, 38], phases: [0.14, 0.08, 0.22],
                 whip: { w: 16, taper: 0.3, amp: 30, waves: 1.2, hz: 3, color: '#e0303a', edge: 'rgba(110,10,20,.9)' }, gap: [0.5, 0.8] } },
    /* 闺4 横绳（躺在绳上从左边滑进来）+ 带线的丢东西（打中罩网兜） */
    T7: { ...g, enter: { kind: 'rope', ends: [[-60, 560], [470, -40]], touch: [128, 212], sag: 16, seq: [['tuck', 0.5], ['idle', 9]] }, exit: { frame: 'tuck' },
          atk: { ...g11.atk, seq: fire4(0.1), hold, tether: { w: 2.5, color: '#6a4b2a' }, onHit: 'net', gap: [0.6, 0.9] } },
  };
  TRIO_BESTIE.ground = {};
  TRIO_BESTIE.groups = [{ name: '飞下+喷', top: 'T4' }, { name: '倒挂+斩痕', top: 'T5' }, { name: '升起+红绸', top: 'T6' }, { name: '横绳+带线+网兜', top: 'T7' }];
})();
