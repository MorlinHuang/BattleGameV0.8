# 用户决定（2026-09-27）：闺蜜还原三个平衡车形象；真相喷雾改为女生档 4，替掉戒指盒

原话：「闺蜜还是还原到之前的三个。新做的真相女神，直接改为第五档礼物，代替之前的礼品盒」
- "第五档" = tier 4（档 0~4 共五档），女生侧 `ITEM_OF.L[4]` 现在是 `'ringbox'`（戒指盒）。
- "之前的三个" = 4ceea80 时的闺蜜：`skins: [1, 2, 3]`、`max: 3`，`CREW.bestie = Bestie`。素材 `bestie3_up|lo|arm.webp` 还在 `web/assets/world/`。

审查角色不改代码。下面是给开发者的改动点（按当前 HEAD b37c821 的行号）和落地后我会复核的判据。

## 一、改动点

| # | 位置 | 现在 | 改成 |
|---|---|---|---|
| 1 | crew.js:500 `MIST.skins` | `[1, 2]` | `[1, 2, 3]`（注释补回 src4 金发双马尾黑比基尼紫平衡车） |
| 2 | crew.js:504 `MIST.max` | `2`（注释写"组合封顶 3 人"） | `3`，注释改回 = 形象数 |
| 3 | crew.js:616 `BestieGroup = CrewGroup([Bestie, Truth])` | 组调度 | 删掉；`CrewGroup` 若无别的使用者一并删 |
| 4 | main.js:1074 `CREW` | `bestie: BestieGroup` | `bestie: Bestie, truth: Truth`（注释同步） |
| 5 | main.js:1110 `ITEM_OF.L[4]` | `'ringbox'` | `'truth'` |
| 6 | main.js:1156 附近 GIFT | 无 truth 行 | 新增 `truth: { name: '真相女神', from: +1, style: 'crew', crew: 'truth', power: 4, recipe: 'truth', push: 600 }`；ringbox 行留作备选（跟花束同一个做法） |
| 7 | main.js:1869 Truth.init 的 onHit | `GIFT.bestie.power`（=3） | `GIFT.truth.power`（=4），否则档 4 首击只有档 3 的份量 |
| 8 | main.js:~1855 Truth 注释 | "闺蜜第三个形象" | 改成档 4；crew.js:576 的注释同理 |
| 9 | 诊断参数 | `?bestie=0|1` 选组成员，`ammogift=bestie&bestie=1` 看真相喷雾 | `?bestie=` 回到原义或删除；胶片要能用 `ammogift=truth` 直接拍 |

注意 giveGift（main.js:287~298）对 tier 4 的数值（`hexDebuff 0.5/8s` + 对方存量减半）在送礼瞬间就结算，跟表现无关，不用动；但原来 tier 4 走 `Ammo.launch(..., {exec:true})` 有 0.55s 全场预警，改成 crew 之后这段预警没了，由她 `enter 0.55 + fire 0.18` 的俯冲出场顶替——见判据 T2。

## 二、落地后的复核判据

| 编号 | 判据 | 怎么测 |
|---|---|---|
| R1 | 闺蜜三个形象都能出现，同屏最多 3 人且不重复 | 蒙特卡洛调度（sched.py）+ live 连刷 `liveGift=boom` |
| R2 | 刷闺蜜不再出现真相喷雾；刷档 4 只出现真相喷雾，不再飞戒指盒 | `live=1&liveGA=boom` / `liveGA=drop` 各跑一段 |
| T1 | 首击份量 = 档 4（power 4），之后轻补 | 读 impact 调用参数 |
| T2 | 档 4 的"质变"没丢：观众一眼能分辨这是比闺蜜贵一档的东西（原戒指盒靠预警 + 1.8 倍体积 + bloom 绽放） | 胶片对比闺蜜 vs 真相喷雾出场前 1 秒；现在她的体量（屏高 ~405px）只比闺蜜（280~380px）大一点，**这一条我预判不过**，建议出场加全屏级的东西（压暗/聚光/名字条），开发者定 |
| T3 | 档 4 连刷（神秘空投 600 连点）时行为明确：她在场时再刷是续时间，不重复、不闪 | live `liveGB`/`liveGA=drop&liveEvery=小值` |
| T4 | **四人同屏**：3 个平衡车闺蜜 + 真相喷雾，这是新出现的组合（原来组合封顶 3）。量脸与身体可见率、女主的脸、气泡走廊 | lab.py 可见率法，5 个姿态；我的站位研究里三人已经偏挤（远排 65~72%），四人是新风险 |
| T5 | 第 1、2 轮已修好的项不回退：喷流可见、尾焰连续、气泡让位（`BUBBLE_TRUTH_DY`）、召回平滑 | 沿用 r2 的复现参数 |

## 三、跟这次决定不冲突、仍然有效的旧结论
- 后腿出画 4.5%（whole 整身转）仍在；用户之前提过要么重出图要么调角度，站位研究 3.2 节的"只转上身"方案依旧适用。
- 闺蜜被女主挡（最差 56~66%）：用户这次选择还原原样，站位研究里的"悬浮抬高"方案未被采纳，不再推。
