# B8 光头伐木工（2026-09-30，第三轮放行后开工）
定妆 ref/B8.png（品红）。品红幕。
- raw/act_a1.png（2x2，参考 ref/B8.png）：idle 缩着、右手在胸前捧着（松果）/ wind **右臂像投手一样举过头顶** / throw 往前下砸 / follow 弯腰喘气摸光头。
- raw/act_b1.png（3x2，参考 act_a1 + ref）：身子朝右（看着追来的熊）、腿往左倒着蹬的倒退跑四帧 + skid 猛回头急刹 + idle。
  同一次出了两张，第二张画成朝左正着跑（不对），用第一张。人只有出手条的 0.82 → prescale 1.22 成 raw/act_b1_x122.png。
  最后一行按"先上后下"排序：先切出来的是站着的 idle2，后面才是 skid（第一次标反，重 build 过）。
- 松果用 3D 图集 prop_pinecone（500273c 返工版），raw/prop_src.png 是返工前临时用的平面松果原图，已不用。
- 跑：过渡帧腾空，不做 walkfix 平移；stride 取 walk1 两只靴前沿横距 188。
