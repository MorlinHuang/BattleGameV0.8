---
name: chashouji
description: 《查手机》弹幕直播玩法的项目总览与导航——玩法定义、代码与素材在哪、怎么起服务、当前做到哪一步、还欠什么。任何涉及"查手机""查岗党/灭迹党""拽手机""BattleGame"的活先读这个，再按它指到对应的 chashouji-art / chashouji-web / chashouji-fx / chashouji-verify / danmu-3d-sprite。新接手这个项目也从这里开始。
---

# 《查手机》项目总览

抖音直播间弹幕互动玩法。一对情侣各拽手机一端来回拉扯，**手机的位移本身就是
对抗线/进度条**；观众刷礼物 = 扔生活物品砸对方。

- **查岗党**（绿 `[126,217,87]`，女方，在左，`from=+1`）——要看手机
- **灭迹党**（红 `[255,72,72]`，男方，在右，`from=-1`）——要删记录

屏幕上**只有角色名与阵营名，永不出现"男队/女队"字样**；聊天内容全是日常短句，
一个露骨的词都没有。胜负绑在"谁先被耗空"这件具体的事上，手机被拽到哪一端是
当下谁力气大。这三条是平台红线要求，改任何文案都不能破。

## 在哪

| | 路径 |
|---|---|
| git 仓库根 | `/workspace/art`（远端 `v08` = `git@github.com:MorlinHuang/BattleGameV0.8.git` main；旧 `origin` 停在 V0.5，不再推） |
| 网页版（**单一真源**） | `/workspace/art/chashouji/web/` |
| 长卷与姿势贴图 | `web/assets/world/`（1.3MB，由 `v14/build.py` 生成） |
| v14 素材管线 | `/workspace/art/chashouji/v14/`（生图原图 + build.py） |
| 旧关键帧（已退役） | `web/assets/frames/` 89 张、`v13/` 管线 |
| 概念图历史 | `/workspace/art/chashouji/v2/ … v9/` |
| Godot 工程 | `/workspace/art/chashouji/godot/battleGame/`（容器副本）<br>用户本机 `D:\Application\godot\battleGame`（真正出 exe 的地方） |
| 截图归档 | `/workspace/art/chashouji/shots/` |

## 怎么跑

网页版 **http://1.14.252.30:40235/index.html**（桌面容器 port-4 = 40235），
桌面容器 `desk-zx2`，SSH 别名 `kf-deployment`（用户 op），`DISPLAY=:1`，
桌面分辨率 1656×960。

```bash
# 增量部署
timeout 100 scp -q main.js fx.js ammo.js bubble.js index.html \
  kf-deployment:/home/op/chashouji/web/

# 推 GitHub（必须带这个环境变量）
export GIT_SSH_COMMAND="ssh -i /workspace/.sshkeys/id_github -o IdentitiesOnly=yes -o UserKnownHostsFile=/workspace/.sshkeys/known_hosts"
timeout 280 git push -q v08 main
```

## 做到哪一步

**2026-09-24 起是 v14 长卷版**（此前的 89 张每 1% 一帧 + 固定客厅已退役，素材还在
`web/assets/frames/` 与 `bg.jpg`，代码不再读）：
- **胜负 = 拖到尽头**：拉力差每秒把两人往拉力大的一边拖，离客厅正中 ±30 米分胜负。
  血条换成**一根距离条**（兼小地图，三间房分段），名字旁写各自拽过来的米数。
- **长卷背景**：女生卧室 | 客厅（左女物右男物）| 暗色电竞房，6700px，镜头跟人走。
  电竞房是暗色，但**特效配色按用户要求没重调**。
- **动作按拉力差选**：僵持（5 张图 8 格循环）→ 落后方跪着 → 往前扑倒 → 趴在地上被拖，两边各一套。
  **被拉倒三档现在各只有一张图 + 颠步占位**，循环帧还没画。
- 受击轻中重的关键图出过（`v14/pose/1*`），**用户说重击太夸张，受击整体暂缓**。
- 素材管线：`chashouji/v14/build.py`（生图原图在 `v14/bg` `v14/pose` `v14/loop`）。

数值体系没动：礼物注入**拉力**、双方对冲、只有**差值**起作用，九档跟平台礼物、表现五档。
X/M/V_Z 的出处与实测见 `chashouji-web` 数值层一节。

## 三个引擎实现

**网页版是单一真源**，Godot 逐字对照搬，不另起炉灶。

| | 状态 |
|---|---|
| 网页版 | ✅ 最新 |
| **Godot 版** | 🔄 停在 `32486d5`（09-17）：弹幕/粒子/气泡/命中链路齐全，但**没跟上**之后网页版的血量制胜负、新 HUD、Q 版结算；**未导出 exe** |

**Unity / 团结引擎版 2026-09-20 由用户决定弃掉**，容器副本与 `chashouji-unity`
skill 都已删除（留在 git 历史里，`git log -- chashouji/unity` 能取回）。用户本机
`D:\Hylyre\BattleGame` 归他自己处置。往后只维持网页版和 Godot 版两个。

**Godot 是为"启动快 + 没有许可证"上的**（用户原话）。它导不出小游戏
（web 导出依赖 SharedArrayBuffer + WASM 线程，抖音/微信容器不提供，官方无支持）——
**目标若改回小游戏，这条路是不通的，不是难是不通。** 细节看记忆
`chashouji-godot-port`；诊断参数 `--selftest / --shot= / --frames= / --click=x,y /
--key= / --nopanel / --nosprite / --live=A,B`。

## 欠的东西（按价值排）

1. **跪 / 扑倒 / 趴的循环帧**（两边各三档，共 6 段）。现在是单张 + 颠步，一眼看得出是占位。
   做法照僵持循环：以现有关键姿势为参考图，逐帧 image-to-image 出 4~5 张来回用。
2. **僵持循环里有两格脚在滑**：nL2 / nR2 两张脚尖相对锚点挪了 40~66px（其余三张 ±14）。
   这是纯生图做循环的已知风险，需要用户看实际效果判断要不要重生这两张。
3. **动作之间是硬切**，没有"被拽倒 / 爬起来"的过渡段。
4. **房间接缝**只是把两扇半门拼在一起，没补完整的门框。
5. **受击轻中重**（暂缓，等用户重新提）。
6. **弹幕池在高火力下饱和**：`MAX = 48`，满了回收队头且不触发命中。见记忆
   `danmu-ammo-pool-saturation`。
7. Godot 版停在血量制之前，整套 v14 都没搬。

## 两条工作纪律（用户定的）

- **特效先在网页测试，用户说"这个特效没问题"之后才同步 Godot。**
- **用户会自己手动改参数**，所以代码要有明确注释。

## 去哪查

| 要干的事 | 看 |
|---|---|
| 角色帧、抠像、概念图、补帧 | `chashouji-art` |
| 改网页代码、加礼物、调数值 | `chashouji-web` |
| 特效、打击感、配色、气泡 | `chashouji-fx` |
| 出/改飞行物品与粒子贴图（3D 渲序列帧） | `danmu-3d-sprite` |
| 看效果、截图、压测 | `chashouji-verify` |
| 同步 Godot、出 exe | 记忆 `chashouji-godot-port` |
