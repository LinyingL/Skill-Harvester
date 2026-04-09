# Skill Harvester — 版本迭代 Handoff

> 这份文档不是 git log。它是**为下一个接手的人写的交接备忘**:每个版本变了什么、为什么变、留下了什么坑、下一个版本应该看哪里。

---

## v4.1 — 2026-04-09 (self-review fixes, doc only)

**主题**:对 v4 self-review 列出的 9 个问题(P0×3 / P1×3 / P2×3)的针对性修订,**不动代码**。

### 起因

v4.5 引入 essence.md 之后, 有了"项目不动点"。这意味着 v4 self-review 的 9 个问题从"项目存亡问题"降级为"技术细节问题" — 但它们**仍然要修**, 否则 v4.1 → 代码阶段会被这些矛盾反咬。

v4.1 是 v4.5 之后的第一份工程修订:**不动 essence, 不动代码, 只修 v4 设计文档自己的内部矛盾**。

### 这一版做了什么

新增 [skill-harvester-design-v4.1.md](./skill-harvester-design-v4.1.md), 在 v4 基础上做以下修订:

#### P0(必修, 三处会让 v4 在第一次跑数据时崩溃的硬伤)

| # | 问题 | v4.1 修订 |
|---|---|---|
| 1 | L4.5 ground truth 矛盾 | **L4.5 改名为 Consistency Checker**;Part B6 措辞从"区分真规则和合理化"降级为"找出内部一致性低的规则";承认 v4 对 review 第 3 条的回应只是部分回应,根本问题留在 open-questions §1 |
| 2 | L3 step 3 违反 hard rule | step 3 改为 **voluntary**(与 step 2 同时呈现, 可跳过);新增 Part B8 假设(员工愿意答 step 3);新增 Phase 0 假设 A8b(自愿率 ≥ 30%) |
| 3 | LOO 在 N=5 时几乎无信号 | 形式化 **N < 9 透明态**:L4.5 不评分, 所有 hypothesis 进 hypothesis 段;A7 阈值从"区分度 ≥ 0.3"降为"严格高于";§11 加 Insufficient sample 失败模式 |

#### P1(应修, 三处影响理解或正确性的不一致)

| # | 问题 | v4.1 修订 |
|---|---|---|
| 4 | MAX_LOOPS = 3 没依据 | 新增 Phase 0 假设 **A9**(L4↔L4.5 迭代收敛性);3 是 Phase 0 之前的占位值, A9 数据出来后校准 |
| 5 | conditions 4 子类边界不清 | conditions 拆为 **trigger / decision** 两段;observable 从分类标签改为标注属性;硬约束"必须 ≥1 个 observable"只限制在 trigger 段 |
| 6 | epistemic × verification 耦合错误 | L5 输出从三段改为 **二维矩阵 4 段**:verified-auto / **verified-but-reminder-only**(v4.1 新增段)/ hypothesis / unlabeled |

#### P1/P2 其余三条

| # | 问题 | v4.1 修订 |
|---|---|---|
| 7 | C2 措辞冲突 ("不被自动化" vs "进 reminder") | Part C 内部分 **enforced** / **best-effort** 两层;C2 降为 best-effort;明确 "automation ≠ reminder" |
| 8 | Subjectivity erosion 不可执行 | §11 明确写出"需要 cli.py 的 monthly_checkin 子命令" — 这是 Phase 1 的具体工作项 |
| 9 | manifest 没有 override 路径 | §10 新增 **override 流程**:显式命令 + reason + 5 秒等待 + audit log + 红色横幅;**永远不能 override 的字段**:delete_owner / portability |

### v4.1 不修的(留给 v5)

- v4 self-review S1/S2/S3/S4(文档结构问题) — 不影响正确性
- v4-open-questions §1 ground truth 鸡生蛋 — 认识论问题, 改名为部分缓解
- v4-open-questions §3 多员工合并 — 范围外
- v4-open-questions §4 UI 漂移检测 — 留 Phase 3
- v4-open-questions §5 manifest 多机器同步 — 留 Phase 3

### v4.1 自己新引入的 open questions

修 9 个问题的过程中, 又冒出两个 v4 没有的新问题, 已加进 [v4-open-questions.md](./v4-open-questions.md):

- **§7 verified 命名诚实**:L4.5 改名为 Consistency Checker 之后, SKILL.md 里 "verified" 标签的语义变弱(从"通过验证"变成"没被检测到不一致"), 这是潜在的承诺过载
- **§8 override 反向激励**:override 流程让"违反 manifest"变成正常工作流, 可能反向削弱规范前提

(原 v4-open-questions §6 元问题被 v4.5 的 essence.md 自动消解, 已替换为新的 §6:essence 与 v4.1 措辞断层)

### Phase 0 假设清单(v4.1 修订)

从 v4 的 9 个增加到 11 个:

| 假设 | 来源 | 内容 |
|---|---|---|
| A1-A6 | v3/v4 沿用 | 任务清单 / LLM 分类 / immediate / deferred / 归纳 / A/B / routine |
| A7 | v4 新增, v4.1 降级 | LOO 在 N≥9 时真规则 consistency 严格高于合理化 |
| A8 | v4 新增 | epistemic_load IRR ≥ 0.6 |
| **A8b** | **v4.1 新增** | step 3 自愿标注率 ≥ 30% |
| **A9** | **v4.1 新增** | L4↔L4.5 迭代在 ≤ 3 轮收敛, ≥ 60% 比例 |

### v4 → v4.1 → 代码工作包

v4.1 把 v4 CHANGELOG 的代码工作包做了细化更新:

| 模块 | v4.1 改动 |
|---|---|
| `models.py` | conditions 改 trigger/decision;新增 verified-but-reminder-only / unlabeled 状态 |
| `consistency_checker.py` | (从 validator.py 改名)实现 N<9 透明态 + §4.4.1 反向闭环状态机 |
| `inducer.py` | LLM prompt 加 trigger/decision 区分 |
| `compiler.py` | 二维矩阵 4 段输出 |
| `dialogue.py` | step 3 改为 voluntary |
| `phase0/data.example.yaml` | 加 A8b / A9 段 |
| `phase0/verify.py` | 加 A8b / A9 scorer |
| `cli.py` | 启动调 deployment gate;新增 monthly_checkin 子命令 |
| `deployment.py` | 新增 override 流程 + 永久不可 override 字段 |

### 文档层次更新

```
essence.md                    ← 项目不动点 (v4.5 引入)
skill-harvester-design-v4.1.md ← ★ 当前的技术参考主文档
skill-harvester-design-v4.md  ← v4.1 取代, 顶部加重定向
skill-harvester-design-v3.md  ← 历史
v4-open-questions.md          ← 8 条 (v4.1 替换 §6, 新增 §7/§8)
CHANGELOG.md                  ← 你正在读的
```

### v4.1 留下的坑

1. **代码还没动**。v4.1 是文档修订, 9 项的实际工程化在下一步
2. **A8b 和 A9 的阈值是拍脑袋数字**(30% 自愿率, 60% 收敛比例) — 跟 v3 的 N=10 一样, Phase 0 数据出来后可能需要校准
3. **override 流程的"5 秒等待 + 红色横幅"是 social friction, 不是技术约束**。如果部署方真的恶意, 这些 friction 都可以被自动化绕过(自动按回车)
4. **Consistency Checker 这个名字不够好**。读者看到 "checker" 仍然会理解成"检查对错"。可能需要 v5 进一步重命名

### 下一步

进 v4.1 → 代码 P0 阶段。具体做法见 v4.1 §6.3。

**重要顺序约束**:
- `models.py` 的 schema 改动**必须最先做**, 因为其他所有模块都依赖它
- `consistency_checker.py` 的反向闭环状态机**必须最后做**, 因为它依赖 dialogue.py 的 step 3 voluntary 改造
- 中间的 inducer/compiler/dialogue 三个可以并行

---

## v4.5 — 2026-04-08 (refocus on what / why / how)

**主题**:不是修订, 是**重新决定文档的层次结构**。

### 起因

v4 self-review 之后, 用户的反馈是: "**最关键的是解决是什么、为什么、和怎么做的问题要搞清楚。技术上的东西可以缓一缓。**"

这一句话指出了一个比 v4 self-review 更深的问题: v3 → v4 的所有 review 都在改"怎么做"这一层(添加 L4.5、改 conditions schema、加 failure modes), 但**没有人停下来问 "这个项目是什么"**。读完 v4 的人能复述七层架构, 但答不出"Skill Harvester 在做一件什么事"。

这是 v3 review 第 1 条(定义张力)的真正后果: v4 修了定义, 但没把"是什么/为什么/怎么做"这三件事**作为文档主轴**。它们仍然是技术架构的注脚。

### 这一版做了什么

新增 [essence.md](./essence.md) — 一份 < 1500 字的纯叙述文档, 三段:

- **是什么**: 一个把你脑子里说不清的判断写下来的工具。
- **为什么**: 因为目前为止, 没有任何工具是站在你这一边的 —— 第一个把"你脑子里的本事"当成你的东西来对待。
- **怎么做**: 你装上它, 它什么都不做地待着, 直到你停下来。然后它在角落亮一下。你可以不理。如果你愿意, 它问你一句话。一句就够。

### 三个产品决定(写 essence 之前钉死的)

essence 不是凭空写的。它建立在三个用户主动选择的产品立场上:

1. **核心不让步的特征 = (a) 用户对自己 skill 的完整控制权**
   - 不是 "提取规则", 不是 "解放生产力", 不是 "新协作范式"
   - 这意味着: 任何威胁控制权的技术能力, 都要让步
2. **目标听众 = (ii) 被采集的员工本人**
   - 不写给雇主, 不写给同行
   - 这意味着: 不能出现 ROI、流程优化、知识资产 这些雇主词汇
3. **风格 = 动作风格**
   - 读完之后读者脑子里是一段电影一样的画面, 不是架构图
   - 这意味着: essence.md 里没有 L0/L1/L2、没有 schema、没有任何参数

之外还有一个写法选择: **Q (纯礼物视角)** vs P (先承认戒心再回应)。用户选了 Q —— essence 假设读者是被价值吸引的, 不是带戒心的, 因此整篇没有"你可能担心..."的防御性句子, 只有"这是你的"的肯定性句子。

### 这一版没做什么

- **没改 v4 design 文档的内容**(只在顶部加了一行指向 essence.md)
- **没改代码**
- **没解决 v4 self-review 列出的 9 个问题**(P0/P1/P2)
- **没出 v4.1**

### 文档层次的新结构

```
essence.md                          ← 项目不动点, < 1500 字, 任何人能读
  └─ 任何 review 先 review 这一份
  └─ 任何新版本先对照这一份检查

skill-harvester-design-v4.md        ← 技术参考, 给工程师
  └─ 顶部一行指向 essence.md

skill-harvester-design-v3/v2/v1.md  ← 历史版本, 不删

CHANGELOG.md                        ← 你正在读的, 项目演化记录
v4-open-questions.md                ← v4 的已知未闭合问题
phase0/                             ← Phase 0 验证工作包
src/skill_harvester/                ← 代码骨架 (v3 schema)
README.md / .de.md / .zh-CN.md      ← 多语言入口
```

**关键变化**: essence.md 现在是"先读这一份"的入口, v4 design 从"主文档"降级为"技术参考"。

### 这一版的逻辑意义

之前所有版本(v1 → v4)的修订模式是 **"在已有文档上递归 review"**。每一轮 review 都让文档更长、更严谨, 但也更难读。v3 → v4 的 60% 篇幅膨胀就是这种模式的代价。

v4.5 改变了这个模式: **不再递归 review 技术文档, 而是另起一个层次**。技术文档继续严谨化(后续 v4.1 / v5 仍然会写), 但它们不再是项目的入口。入口是 essence.md, 它的修订门槛极高 —— 只有当"是什么/为什么/怎么做"这三件事真的变了, 才会改。

这相当于给项目第一次定义了一个**不动点**。有了不动点之后:

- 任何新批评都先问 "它打的是 essence 还是 v4 的某个细节"
- 打 essence 的批评是大事, 必须正面处理
- 打 v4 细节的批评是小事, 可以慢慢迭代
- v4 self-review 列出的 9 个问题, 现在全部归类为 "v4 细节" —— 它们仍然要修, 但不再是项目的存亡问题

### v4.5 留下的坑

1. **essence.md 没有被用户实际验证过**。它写完之后, 应该被一个真实的目标用户(一名客服 / 一名运维 / 一名分析师)读一遍, 然后被问 "你读完之后想用这个东西吗"。回答是 yes 或 no 都比"我自己觉得它写得对"重要
2. **v3 README 的多语言版本(中英德三语)没有更新指向 essence.md**。下一步应该加入 essence 的中英德三语版, 因为 essence 的目标读者是员工, 而员工的母语很可能不是英语
3. **v4 self-review 的 9 个问题仍然挂着**。v4.5 的存在不是为了避免修它们, 是为了让修它们时知道"哪几条会动到 essence, 哪几条只动 v4"
4. **essence.md 和 v4 design 的"How"段落不一致**。essence 说"在角落亮一下, 你可以不理", v4 §4.5.1 immediate 层是"自愿触发的红点"—— 两者意思一样, 但措辞不同。读者从 essence 跳到 v4 时会感到风格断层。这是预期内的(两份文档的目标读者不同), 但需要在 v4.1 修订时让 v4 的措辞至少**不否定** essence

### 下一步

不要直接进 v4.1 或代码。下一步应该是:

1. **找一个真实的目标用户读 essence.md**, 看反应
2. 如果反应是 "这是给我的", 进 v4.1 修 self-review 的 9 个问题, 然后进代码
3. 如果反应是 "这不是我想要的", **回到 essence.md, 不是回到 v4** —— 因为问题在不动点上, 不在技术上

---

## v4 — 2026-04-08 (design only, no code yet)

**主题**:对一份十条逻辑 review 的正面回应。这一版**只动文档**,不动代码 —— 走的是 v3.1 之后约定的"路径 B":先达成设计共识,再动手实现。

### 这一版回应的 review

完整的 review 是 v3 之后收到的最严肃的一次,因为它打的不是组件,是**论证结构本身**。十条压成一句话:

> v3 把"技能提炼"讲得像是从 tacit 到 rule 的自然过渡, 但实际上这中间隔着五座桥:**可表达性 / 可形式化性 / 可验证性 / 可迁移性 / 控制权归属**, 全部用直觉滑过去了。

### 变更摘要

| 类别 | 内容 |
|---|---|
| 设计文档 | 新增 [skill-harvester-design-v4.md](./skill-harvester-design-v4.md) — **整篇按 描述/设计/规范 三段重组**,不是补丁 |
| 开放问题 | 新增 [v4-open-questions.md](./v4-open-questions.md) — 6 个 v4 主动承认未闭合的深层问题,作为 v5 输入 |
| 代码 | **本版本不动代码**。v4 落地的代码工作清单在下方"v4 → 代码 工作包"里 |

### 逐条回应这十条

| # | 批评 | v4 怎么回应 |
|---|---|---|
| 1 | Skill 定义张力(压缩 vs 重构) | §0.1 收窄定义为 elicit/abstract/formalize/delegate 四步;"compilation 反向" 隐喻降级 |
| 2 | Knowing How ≠ IF-THEN | §0.2 显式声明 IF-THEN 是 partial representation;表达力损失由 LLM Agent 那一层兜底,不由 Skill Harvester 兜底 |
| 3 | 对话 → 规则缺有效性证明 | **★ 新增 L4.5 Hypothesis Validator**(v4 最大改动)—— replay test 把 production 从"故事"变成"假设",L3↔L4↔L4.5 闭环最多迭代 3 轮 |
| 4 | 假二分(event vs rule) | Part A §A5 修正:event trace 是证据来源,production hypothesis 是目标表示。两者不是对立 |
| 5 | circumstances 没有形式边界 | §4.3 conditions 字段从 `list[str]` 升级为 typed schema(observable / declared / organizational / exception_only),硬约束:必须至少有 1 个 observable |
| 6 | "可自动化"→"应自动化"规范跳跃 | §0.4 规范前提显式化为 non-negotiable;§10 deployment manifest gate 把它落到 CLI 拒启动层级 |
| 7 | 个人赋能 vs 知识抽取的判别条件 | Part C 5 项控制权(visibility/edit/delete/portability/sharing consent)+ deployment_mode.yaml |
| 8 | 重复 vs 创造性的二分太粗 | §0.2 non-goals 加 "epistemic function";L3 step 3 让员工标 epistemic_load;L5 三段输出(verified/hypothesis/**reminder**)— 高 epistemic_load 永不自动执行 |
| 9 | 描述/设计/规范命题混在一起 | **整篇文档按 Part A/B/C 三段重组**。每一段证明负担、检验方式、修订门槛都不同 |
| 10 | 缺少失败条件 | **§11 Failure Modes 表** — 7 种失败模式,每一种有可观测信号 + 明确的系统行为 |

### v4 的核心新结构

#### 三段命题分离(Part A/B/C)

```
Part A 描述性命题  ← 已知事实, 修订门槛 = 新实证证据
  - 5 条带文献引用 (Polanyi / Anderson / Klein / Ericsson / van der Aalst / Nisbett & Wilson)

Part B 设计假说    ← 可证伪的, 修订门槛 = Phase 0 数据
  - 7 条, 全部对应 Phase 0 假设 A1-A8 (v4 新增 A7/A8)

Part C 规范约束    ← 不可妥协, 修订门槛 = 伦理论证
  - 4 条 (5 项控制权 / epistemic function 不自动化 / 默认不评价监控 / 可降级)
```

#### 七层架构(v3 六层 + L4.5)

```
L5   Skill Compiler            verified / hypothesis / reminder 三段输出
L4.5 Hypothesis Validator   ★  replay test, 反向触发 L3
L4   Production Inducer        输出 ProductionHypothesis (改名), conditions 类型化
L3   Dialogue Engine           三时延 + step 3 epistemic_load 标注
L2   Episode Builder
L1   Sparse Sensor
L0   Task Catalog
```

#### Phase 0 扩充(7 → 9 假设)

| 新增 | 内容 |
|---|---|
| **A7** | replay test 在小样本下能区分真规则 / 合理化规则 / 错规则 (区分度 ≥ 0.3) |
| **A8** | epistemic_load 标注的 test-retest ≥ 0.7 且 IRR ≥ 0.6 |

### v4 主动承认的 6 个未闭合问题

完整内容在 [v4-open-questions.md](./v4-open-questions.md):

1. **Replay test 的 ground truth 鸡生蛋问题** — 最基础,撑不住的话 L4.5 整个失效
2. epistemic_load 的主观漂移和策略性标注
3. 多员工版本的规则合并裁决
4. UI 漂移检测的反向触发链路
5. deployment manifest 在多机器同步场景下的一致性
6. (元问题)v4 文档严谨化后牺牲的叙事吸引力

**这一份"主动承认"是 v4 设计原则 §11 的体现:一个理论必须能宣告自己失败,同样一个设计必须能宣告"这里我还不知道"。**

### v4 → 代码 工作包(下一步)

设计共识达成后,v4 → 代码需要做的事:

| 模块 | 改动 | 优先级 |
|---|---|---|
| `models.py` | `Production` → `ProductionHypothesis`;`conditions` 升级为 typed schema(4 个子类);新增 `epistemic_load` / `replay_accuracy` 字段 | P0 |
| `validator.py` | **新文件** — L4.5 replay test (leave-one-out);反向触发 L3 队列 | P0 |
| `deployment.py` | **新文件** — manifest 加载 + CLI gate;违反规范前提则 raise | P0 |
| `inducer.py` | 输出 ProductionHypothesis 而不是 Production;LLM prompt 加 typed conditions 约束 | P0 |
| `compiler.py` | 三段 SKILL.md 输出(verified / hypothesis / reminder) | P1 |
| `dialogue.py` | L3 step 3 — epistemic_load 标注问题 | P1 |
| `phase0/data.example.yaml` | 加 A7 / A8 段 | P1 |
| `phase0/verify.py` | 加 A7 / A8 scorer + 阈值 | P1 |
| `cli.py` | 启动时调用 deployment gate | P0 |

**建议执行顺序**:P0 全部一次性做完(因为它们互相依赖,半截状态会破坏 v3 的 smoke test),然后分批做 P1。

### v4 留下的坑

(除了 v4-open-questions.md 里的 6 条之外)

1. **没有真实数据**。Phase 0 还没跑过,9 个假设全部是纸上的。v4 的所有 "+20pp" "区分度 ≥ 0.3" 都是拍脑袋数字
2. **L4.5 的 replay test 计算成本未估算**。leave-one-out × N 个 hypothesis 在每周一次的批处理里能不能跑完,没算过
3. **v4 文档很长**。比 v3 多约 60%。读者疲劳是真实风险

### 下一个接手的人请先做这件事

**不要直接动代码**。先做这两件事:

1. **完整读一遍 [skill-harvester-design-v4.md](./skill-harvester-design-v4.md)**,特别是 Part A/B/C 三段的命题分类。确认你理解 "为什么 v4 不是 v3 的补丁" — 如果你还把它当补丁,后面的代码工作会偏
2. **完整读一遍 [v4-open-questions.md](./v4-open-questions.md)** 第 1 条。如果你对 "ground truth 鸡生蛋" 没有清晰立场,L4.5 不要动手 — 因为你写出来的代码会在第一次跑真实数据时被这个问题打回

只有这两件事都做完,才动代码。否则就是浪费工程预算。

---

## v3.1 — 2026-04-07 (tooling)

**主题**:Phase 0 验证工作包落地。不动设计文档,只补一份"7 天能跑完"的实验流程 + 评分脚本。

### 变更摘要

| 类别 | 内容 |
|---|---|
| 工作包 | 新增 [phase0/](./phase0/) 目录:`README.md` + `data.example.yaml` + `verify.py` |
| 评分阈值 | `verify.py` 顶部的 `THRESHOLDS` 字典与 design v3 §1 一一对应,任何调整必须先改设计文档 |
| CI gate | `verify.py` 在任何假设 FAIL 时返回 exit code 1,可以放进 pre-Phase-1 的硬卡口 |

### 设计决定

1. **3 个文件,不是 16 个**。本来想给每个假设一个独立模板/脚本,显式列在 README 里。后来改成单一 `data.yaml` + 单一 `verify.py`,理由:Phase 0 的瓶颈是"有没有人愿意花一周跑",不是"工程优雅"。文件越少越容易开始。
2. **示例数据全部 PASS**。`data.example.yaml` 里填的是一份"理想结果",让用户复制后能立刻看到"通过的样子",再去对照修改。
3. **FAIL 时打印备选方案**。每个 hypothesis 的 fail 路径都对应 design v3 §1 表格里的"不通过的备选方案",直接显示在 panel 里,避免用户还要回去翻文档。
4. **`--only A2` 支持单跑**。Phase 0 的 7 天节奏里,每天只完成 1-2 个假设的数据收集,单跑能让用户当天就看到反馈。
5. **没有写 pytest**。这一份是"实验记录工具",不是"被测代码"。它的正确性由 `data.example.yaml` 全 PASS + 故意造的坏数据 FAIL 这两个手动 smoke test 保证(README 里有命令)。

### 怎么用

```bash
cd phase0/
cp data.example.yaml data.yaml
# 按 README 的"7 天执行节奏"逐天填数据
python verify.py
# 看 PASS/FAIL 表格 + FAIL panel 里的备选方案
```

### v3.1 留下的坑

1. **A1 的 `vague_count` 是评估者主观判断**,没有客观标准。理论上应该让两个独立评估者打分算 IRR,但 Phase 0 阶段不值得这么重的流程。如果将来发现"不同人评估的 A1 结果差异很大",再补客观标准
2. **A4 的 `peer_endorsed` 同样是主观的**。这是设计上的妥协 —— 让另一名同岗位员工"认可"一条规则本来就没有客观尺度。降低主观性的方法只能是 A5(让 Agent 真去用,看一致率),而 A5 已经在表里
3. **`info_score` 是 1-5 主观打分**。心理学研究里这种 Likert 量表有已知偏差(中心趋势、社会期望)。Phase 0 阶段接受这个误差,Phase 1 末尾的端到端 A/B 才是真正的客观验收
4. **没有"目标用户选择"的硬性指引**。Phase 0 README 假设你已经选好了一名员工。但"选谁"这件事本身可能决定 A1/A6 的结果 —— 选了一个工作过于碎片化的员工,A1 注定 fail。下一版可以加一份"目标用户筛选清单"

### 下一步

跑完一轮真实 Phase 0 后,把 `data.yaml` 和 `verify.py` 的输出截图作为 v3 → v4 的输入证据,在本 CHANGELOG 顶部新建 v3.2 章节记录结论。

---

## v3 — 2026-04-07

**主题**:对 v2 的五条核心 review 批评做正面回应,补两条触发线和三时延对话框架。

### 变更摘要

| 类别 | 内容 |
|---|---|
| 设计文档 | 新增 [skill-harvester-design-v3.md](./skill-harvester-design-v3.md) |
| 架构 | L1 新增频率累加器 + 长时元数据缓冲;L2 新增 routine 触发线;L3 拆三时延档 |
| 模型 | `Episode` 增加 `recent_metadata` / `routine_signature`;`TriggerKind` 枚举 |
| 代码 stub | 新增 `routine_detector.py` + `tiered_dialogue.py`(标记为 Phase 1.5) |
| 假设 | A3 拆为 A3a/A3b;新增 A6(routine 触发可行性) |
| 路线图 | Phase 0 增加 A3a/A6 验证项;Phase 1 增加两个 stub 模块 |

### 这一版回应的具体批评

| # | 批评 | v3 怎么回应 |
|---|---|---|
| 1 | 黄金时刻悖论:漏阴性 | L1 sensor B + L2 触发线 B,正交于 surprisal 抓"已经压实的产生式" |
| 2 | 微观记忆衰减 | L3 三时延档,immediate 层用自愿红点抓 0-30s 瞬时记忆 |
| 3 | 因果链断裂 | recent_metadata 把因果窗口从 30 秒扩到 15 分钟,只存元数据无截图 |
| 4 | 过度线性化 | §0.1 明确 SKILL.md 是 LLM prior 而非硬规则;§0.2 加 non-goals 清单 |
| 5 | L0 自举悖论 | §4.2 把"L0 动态生长"提到节首,作为预防性回答 |

### v3 留给下一个版本的坑

1. **routine_detector 的 N 和冷却期是拍脑袋数字**(N=10,冷却 30 天)。Phase 0 必须实测校准
2. **tiered_dialogue 的 immediate 层 stub 没有 GUI**,只能在终端 attach 时弹。真实使用需要系统级红点托盘 — Phase 2 工作
3. **window_template 归一化**目前用最朴素的"数字替换为 #N"。对中文窗口标题、对动态 ID(如 UUID)效果差,需要按目标 app 写规则
4. **A3a 假设没有验证**:0-30 秒的"自愿红点"在真实工作场景下能不能有 ≥10% 触发率,完全是一个假设。如果触发率太低,immediate 档形同虚设,v3 的批评 2 修复就只剩 close-window 一档,效果会打折
5. **recent_metadata 在 LLM prompt 里的最佳塞法没试过**:塞太多会污染 prompt 主轴,塞太少又起不到因果作用。Phase 1 跑通后第一件事就是调这个

### 下一个接手的人请先做这件事

跑一次 smoke test,确认 v3 的代码改动没破坏 v2 的端到端链路:

```bash
cd /Users/lilinying/Downloads/Skill-Harverster
SKILL_HARVESTER_HOME=/tmp/sh-test SKILL_HARVESTER_LLM=mock python -m skill_harvester.cli status
```

然后看 [skill-harvester-design-v3.md 附录 A](./skill-harvester-design-v3.md#附录-av3-相对-v2-的关键变化),逐条对照代码检查是不是都落地了。**特别注意**:v3 的 stub 模块只是接口,L1 sensor B 和 L3 immediate 层都还没真正接入 capture loop,需要 Phase 1.5 的工作把它们串进来。

---

## v2 — 2026-04-07

**主题**:对 v1 的多轮 review 做结构性修订,把循环依赖和验收路径补上。

### 变更摘要

| 类别 | 内容 |
|---|---|
| 设计文档 | 新增 [skill-harvester-design-v2.md](./skill-harvester-design-v2.md) |
| 代码 | 全新建立 Phase 1 骨架(`src/skill_harvester/`,7 个模块 + CLI) |
| 架构 | 新增 L0 Task Catalog 层;L3 拆 step1(分类)+ step2(追问);L4 改意图/执行双层 |
| 路线图 | 新增 Phase 0 可行性证伪阶段(零代码);Phase 1 验收改为端到端 A/B |
| 合规 | 新增个人模式/团队模式双部署,绕开 BetrVG §87 风险 |

### 这一版解决了 v1 的什么

| v1 问题 | v2 怎么解 |
|---|---|
| L1/L2 默认 goal 已知,但没人负责 goal 识别(循环依赖) | 引入 L0 Task Catalog 作为元数据基座;Episode schema 移除 `goal_hint` |
| 没有 Phase 0,假设风险全堆在 Phase 1 | 新增 Phase 0,1 周纸笔 + LLM 验证 5 个假设 |
| L4 直接归纳到 UI 动作,UI 漂移 = skill 报废 | Production 拆 intent / execution 双层,UI 漂移只重写 execution |
| L1 用 n-gram 算 novelty(脆弱) | Phase 1 不算 novelty;Phase 2 改用 AX Tree 拓扑变化 |
| Phase 1 验收"编出 1 条 SKILL.md"过于主观 | 改为端到端 A/B:Agent 用 skill vs 不用,一致率差 ≥ 20pp |
| 隐私合规放 Phase 3,德国市场会卡死 | 双部署模式,Phase 1/2 走个人模式绕开 Betriebsrat |

### v2 留下、v3 要补的坑(就是 v3 的工作)

1. 黄金时刻悖论:漏阴性(已压实产生式没有 surprisal)
2. 微观记忆衰减:下班前问 = 事后合理化
3. 因果链断裂:30 秒环形缓冲不够
4. SKILL.md 给谁用没说清,导致"线性化必崩溃"的误读
5. L0 动态性藏在文档中段,导致"自举悖论"误读

### 这一版的代码骨架长什么样

```
src/skill_harvester/
├── models.py        # TaskCatalog / Episode / Production (intent+execution)
├── storage.py       # ~/.skill-harvester/ JSONL 持久化
├── llm.py           # mock / anthropic / openai 三后端
├── capture.py       # L1+L2 最笨版本:全局热键 + 截屏
├── classifier.py    # L3 step 1:LLM goal 分类
├── dialogue.py      # L3 step 2:CLI 反事实追问
├── inducer.py       # L4:按 task_id 分组 + 双层归纳
├── compiler.py      # L5:SKILL.md 编译
└── cli.py           # init / capture / review / induce / compile / status
```

Smoke test 通过(mock 后端 → 端到端 SKILL.md 输出)。

---

## v1 — (原始版本,日期未知)

**主题**:首次提出 Skill Harvester 的认知科学叙事和五层架构。

### 这一版立住了什么

- **核心叙事**:Skill 不是行为录音,是判断的化石
- **理论根基**:Polanyi tacit knowledge / Anderson ACT-R / Klein RPD / Zacks event segmentation / Shannon
- **五层架构**:L1 Sparse Sensor → L2 Episode Builder → L3 Dialogue Engine → L4 Production Inducer → L5 Skill Compiler
- **关键差异化**:不是 RPA,不是 task mining,因为有 L3 反事实对话
- **反向开发原则**:从 L5 倒着做,不要先做 L1/L2 的工程

### v1 留下的问题(v2 已解决)

见 v2 的"这一版解决了 v1 的什么"表格。

---

## 怎么读这份 handoff

- **找最新状态** → 看顶部最新版本的"变更摘要"和"留下的坑"
- **追溯一个设计决定的来源** → 沿着各版本的"这一版回应/解决了什么"往下挖
- **接手 v3 之后** → 先按 v3 的"下一个接手的人请先做这件事"跑 smoke test,然后挑一个"留下的坑"开工

每出新版本,在顶部追加一个章节,**永远不要删除老版本的记录**。这份文档的价值正在于"看着它长大"。
