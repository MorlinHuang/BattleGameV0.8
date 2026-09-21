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
| git 仓库根 | `/workspace/art`（远端 `git@github.com:MorlinHuang/BattleGame.git` main） |
| 网页版（**单一真源**） | `/workspace/art/chashouji/web/` |
| 角色帧成品 | `web/assets/frames/` 共 89 张 960×900 PNG（49MB） |
| v13 素材管线 | `/workspace/art/chashouji/v13/`（raw 入库，中间产物可重跑） |
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
timeout 280 git push -q origin main
```

## 做到哪一步

网页版三层都在跑：预渲染关键帧角色 + 对抗线/刻度 + 弹幕/粒子/气泡。
礼物与数值体系已落地：礼物注入**拉力**，双方拉力对冲，只有**差值**起作用 ——
差值决定手机被拽到哪（瞬时读数，会走回来），差值每秒扣对方的血，**血量归零者负**
（`2a8db47` 起；此前是手机位置到端点判胜）。数值九档跟平台礼物、表现五档。
设计、X/M/Z 的出处与实测见 `chashouji/docs/数值设计.md` §八。
上一版（`0a1e678` 自发光弹道、聊天气泡、顿帧不应期）**用户评价：60 分**。

## 三个引擎实现

**网页版是单一真源**，Godot 逐字对照搬，不另起炉灶。

| | 状态 |
|---|---|
| 网页版 | ✅ 最新 |
| **Godot 版** | 🔄 玩法层与表现层都跑通了（弹幕/粒子/气泡/命中链路齐全）；**未导出 exe** |

**Unity / 团结引擎版 2026-09-20 由用户决定弃掉**，容器副本与 `chashouji-unity`
skill 都已删除（留在 git 历史里，`git log -- chashouji/unity` 能取回）。用户本机
`D:\Hylyre\BattleGame` 归他自己处置。往后只维持网页版和 Godot 版两个。

**Godot 是为"启动快 + 没有许可证"上的**（用户原话）。它导不出小游戏
（web 导出依赖 SharedArrayBuffer + WASM 线程，抖音/微信容器不提供，官方无支持）——
**目标若改回小游戏，这条路是不通的，不是难是不通。** 细节看记忆
`chashouji-godot-port`；诊断参数 `--selftest / --shot= / --frames= / --click=x,y /
--key= / --nopanel / --nosprite / --live=A,B`。

## 欠的东西（按价值排）

1. **对抗线与手机位置错位**：p=0 时线在 x=566、手机在 740，差 174px。
   修它要手工标 89 帧的手机坐标。
2. **角色帧有两处硬伤，是同一个根因**（2026-09-20 逐张核对，数据见记忆
   `chashouji-keyframe-frames`）：
   - **手机朝向在 0~100 上翻转 6 次**（20/22/26/35/40/80），29 张生图从没在
     prompt 里约束过手机怎么拿，模型每张自由发挥；40~44 还是唯一屏幕正面朝
     观众的一段。
   - **101 档实际只有 89 张**，缺 `21,23,24,61,81,83,84,86,96,97,98,99` —— 7 对
     相邻生图档差异超 `MAX_DIFF=42` 不给插，缺档映射到邻居 = 硬切，最糟的
     95→100 一次跳 68.5%。
   **"补密到每 0.5% 一张"对这两条都无效**：缺的不是密度，是两张姿态能对上的
   生图。顺序必须是 统一朝向+补断点生图 → 再谈密度。
3. **弹幕池在高火力下饱和**：`MAX = 48`，满了回收队头，而被回收的那一发
   **不触发命中也不产生粒子**。实测每帧发射超过 1.8 发（约每秒注入 1500~2000，
   相当于每秒三个神秘空投）就一发都命中不了 —— 屏幕上弹幕最多的时候，打击感
   反而整个消失。三个引擎同此逻辑。见记忆 `danmu-ammo-pool-saturation`。
4. 手机屏幕内容烧死在帧里，没法动态显示聊天记录——这是选关键帧路线时接受的代价。
   **把手机独立成一层**能同时解掉这条、第 2 条和第 3 条的朝向问题。遮挡顺序不是
   障碍（每一档手指都绕到手机正面，手机层画在角色层之下就自然被盖住），但它
   **省不掉重出生图**：手指位置是按原手机的形状画的，换贴图会抓空。另外要抠掉
   89 张里的旧手机并 inpaint，且位置/角度只能手工标（自动检测实测不可用）。

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
