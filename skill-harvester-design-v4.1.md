# Skill Harvester — 项目设计文档 v4.1

> **这是技术参考文档。如果你想知道这个项目"是什么 / 为什么 / 怎么做",请先读 [essence.md](./essence.md) — 那才是项目的不动点。本文档只解释"技术上具体怎么实现"。**
>
> **v4.1 修订说明**:这一版是对 v4 自检发现的 9 个问题(P0×3 / P1×3 / P2×3)的针对性修订,**不是 v5**。v4 的整体结构(Part A 描述 / Part B 设计 / Part C 规范 / Part D 架构 / Part E 路线 / Part F 失败模式)继续成立,只在以下三类位置打补丁:
>
> 1. **L4.5 的本质重定位**:从 "Hypothesis Validator" 改名为 "Consistency Checker",B6 措辞降级,§4.4 重写
> 2. **三处自相矛盾的修复**:CHANGELOG v4 的回应表过度承诺、Part C C2 与 §4.5 的措辞冲突、§4.4 与 §4.5 关于 hypothesis 流向的描述不一致
> 3. **三个边界不清的概念形式化**:typed conditions 拆 trigger / decision、L5 verification × epistemic 二维矩阵、Part C enforced / best-effort 分层
>
> 完整的 self-review 9 条修复对照见 §附录 A。
>
> v4 文档保留在仓库里作为对照:[skill-harvester-design-v4.md](./skill-harvester-design-v4.md)。

---

## 0. 核心信念

### 0.1 Skill 的收窄定义

> **Skill 是可重复实践能力中,那些能够被诱导表达(elicited)、抽象(abstracted)、形式化(formalized)、且委托执行(delegated)的部分。**

(沿用 v4 §0.1)

### 0.2 SKILL.md 是什么、不是什么

(沿用 v4 §0.2)

### 0.3 三步分解图

```
[L3 step 2] elicit       — 反事实对话, 把 tacit 变成 partial articulation
[L4]        abstract     — 跨 episode 抽出候选规则
[L4.5]      check        — consistency check, 不是真理裁判          ★ v4.1 改
[L4]/[L5]   formalize    — 用 typed conditions schema 写出可证伪的 production
[L5]        delegate     — 编译成 SKILL.md, 进入 Agent 调用入口
```

**v4.1 关键修订**:把 L4.5 的动词从 "validate" 改为 "check"。这一字之差对应 §4.4 的全面重写 —— 见下文。

### 0.4 规范前提(non-negotiable 总纲)

> **自动化的收益、控制权与节省时间应主要归属于执行者本人。在这个前提不成立的部署里,Skill Harvester 不应被使用。**

**v4.1 修订**:删除 v4 §0.4 末尾"5 项控制权"的预告。具体的 enforced / best-effort 拆分见 Part C。

### 0.5 v4.1 范围声明【新增】

v4.1 在 v4 之上叠加,**v3 对 review 批评 1-5 的回应在 v4/v4.1 里继续有效**:

- v3 引入 sensor B(频率累加器)回应批评 1(漏阴性)
- v3 引入 recent_metadata 15min 缓冲回应批评 3(因果链断裂)
- v3 引入 L3 三时延对话回应批评 2(微观记忆衰减)
- v3 强化 L0 动态生长回应批评 5(自举悖论)
- v3 §0.1 声明 SKILL.md 是 LLM prior 回应批评 4(过度线性化)

**v4 不重新论证这些**,只新增对一份十条逻辑 review 的回应。**v4.1 不重新论证 v4 的 9 项,只修自检发现的内部矛盾**。

---

# Part A — 描述性命题(Descriptive)

> v4.1 修订说明:Part A 只放真正没争议的事实。**有争议的研究结论挪到 Part B 作为相应假说的依据**,不再以"已知事实"的姿态出现。
>
> Part A 的修订门槛:出现新的实证证据。

## A1. 人类技能有大量 tacit 与 procedural 成分

- **证据**:Polanyi 1966 *The Tacit Dimension*;Anderson 1983/1993 ACT-R 双系统;Dreyfus & Dreyfus 1986 五阶段技能模型
- **争议程度**:低(认知科学公认)
- **对设计的含义**:任何依赖"让专家描述自己怎么做"的方法都会丢掉已下沉到 procedural 层的部分

## A2. 已压实的产生式没有 surprisal 信号

- **证据**:Klein RPD;ACT-R 三阶段
- **争议程度**:低
- **对设计的含义**:仅靠 surprisal 触发器会系统性漏掉最有价值的产生式 → v3 sensor B 的依据

## A3. 事后回忆质量随时间衰减(★ v4.1 改:降级为"普遍承认的现象")

- **证据**:Ebbinghaus 遗忘曲线;Ericsson & Simon 1980 *Protocol Analysis*
- **争议程度**:**中**。"衰减"本身是事实,但"衰减后的报告就是事后合理化"是更强的命题,有争议
- **v4.1 修订**:这条只保留"衰减"的弱版本。"自我报告 ≠ 真实驱动机制"的强版本(原 v4 §A4)**移到 Part B 作为 B6 的依据**,不再作为 Part A 的事实
- **对设计的含义**:L3 三时延对话的依据(瞬时记忆型问题必须 immediate)

## A4. event trace 是 rule discovery 的合法证据来源(★ v4.1 改:从 Part A 挪到 Part D §4.0)

**v4.1 修订**:这一条原 v4 §A5 实际上是论辩性命题(在反驳 v3 review 第 4 条),不是描述性事实。**整条移到 Part D §4.0 作为 "Skill Harvester 与 RPA 的关系" 的开场**。Part A 不再有这一条。

---

# Part B — 设计假说(Design hypotheses, falsifiable)

> v4.1 修订:增加 B0;B6 措辞降级;每条假说后明确写出**它依赖的 Part A 事实**和**它在 Part A 之外的额外假定**。
>
> Part B 的修订门槛:Phase 0 / Phase 1 实测数据。

## B0【v4.1 新增】员工能写出动宾结构的日常任务清单

- **依赖**:无
- **额外假定**:目标用户的工作具有可被语言切分的任务结构(过于碎片化的工作不满足)
- **验证**:Phase 0 假设 A1
- **v4.1 加这一条的原因**:v4 漏了 A1 在 Part B 的对应,导致 design 文档和 phase0 工具说的不是同一组假设

## B1. 一部分 tacit knowledge 可通过对话 + 案例校正转为可执行表示

- **关键限定**:**一部分**,不是全部
- **依赖**:Part A1
- **额外假定**:可被表达的部分占比足够大,以至于 SKILL.md 输出对 Agent 有用(由 Phase 0 A5 验证)
- **验证**:Phase 0 假设 A4 + A5

## B2. LLM 在 L0 task catalog 约束下能做高置信度 goal 分类

- **依赖**:无
- **验证**:Phase 0 假设 A2

## B3. immediate 一句话快问能在不打扰前提下抓瞬时记忆

- **依赖**:Part A3 弱版本(衰减)
- **额外假定**:0-30s 是"瞬时"窗口
- **验证**:Phase 0 假设 A3a

## B4. deferred 对比追问不依赖瞬时记忆

- **依赖**:Part A3 弱版本
- **额外假定**:对比追问依赖的是规律记忆(语义记忆),不是情景记忆 — 这是认知心理学常识,但在小时级延迟下是否成立需要数据
- **验证**:Phase 0 假设 A3b

## B5. routine 频率累加器能找到已压实的 high-value 产生式

- **依赖**:Part A2
- **验证**:Phase 0 假设 A6

## B6【v4.1 改】replay test 能找到内部一致性低的规则(consistency check)

**v4 原措辞**:"replay test 能区分真规则和事后合理化"

**v4.1 措辞**:"replay test 能找到一种规则:它解释了它训练时见过的 episode,但解释不了同 task 内它没见过的 episode。这种规则更可能是过拟合或事后合理化的产物,但 replay 不能反过来证明通过 replay 的规则就是真规则。"

- **依赖**:Nisbett & Wilson 1977(原 Part A4 命题,**作为依据出现而不是事实**)
- **额外假定**:员工历史 episode 的实际 action 在多数情况下足够近似 ground truth(这一假定的局限性见 v4-open-questions §1)
- **v4.1 关键变化**:命题从"双向验证"降级为"单向过滤"。一条规则**不通过** replay 是有意义的负面信号(它至少不一致);**通过** replay 不构成正面证明(它只是没被检测到不一致)
- **验证**:Phase 0 假设 A7(在 v4.1 中也降级,见 §6.2)

## B7. 员工能可靠地标注 epistemic_load(标注一致性)

- **依赖**:无
- **额外假定**:员工的 epistemic_load 标注**在不被系统行为反向影响的条件下**保持一致
- **验证**:Phase 0 假设 A8

## B8【v4.1 新增】员工愿意对 reviewed episode 做 epistemic_load 标注

- **依赖**:无
- **v4.1 加这一条的原因**:v4 §4.2 让 L3 step 3 在每条 reviewed episode 上追加一个 epistemic_load 标注问题,但没问"员工愿不愿意答这个问题"。这违反 v4 §4.5.3 的 hard rule "永远不强制打断"
- **解决方式**:step 3 改为 voluntary,与 step 2 同时呈现,可跳过
- **验证**:Phase 0 假设 A8b(v4.1 新增,见 §6.2)

---

# Part C — 规范约束(Normative constraints)

> v4.1 修订:Part C 内部分两层 — **enforced**(代码 gate 可拒启动)和 **best-effort**(承诺,但实现取决于其他不可靠环节)。这是为了诚实回答"哪些规范是真正硬约束,哪些只是表态"。

## C-enforced(代码层硬约束)

### C1. 用户对自己 skill 的 5 项控制权(default = employee)

| 权利 | 默认归属 | manifest 字段 | enforced |
|---|---|---|---|
| Visibility | employee | visibility_owner | ✓ |
| Edit | employee | edit_owner | ✓ |
| Delete | employee | delete_owner | ✓ |
| Portability | true | portability | ✓ |
| Sharing consent | explicit | sharing_consent | ✓ |

**enforcement**:启动时 §10 deployment manifest gate 检查这 5 项,任何一项被改成违反默认值的形式 → 进入 §10 override 流程(v4.1 新增,见下文)。

### C3a. 默认不用于评价 / 监控

- `use_for_evaluation: false`(默认)
- `use_for_monitoring: false`(默认)
- 这两条改成 true → 触发 §10 override 流程

## C-best-effort(承诺,但依赖不可靠环节)

### C2. epistemic function 不被自动化(★ v4.1 改:从 enforced 改为 best-effort)

**v4 原措辞**:"承担 epistemic function 的重复动作 **不应被自动化**"(non-negotiable)

**v4.1 措辞**:
> 承担 epistemic function 的重复动作**默认不进入自动执行段, 只进入提醒段**。系统的判定依据是 L3 step 3 的员工 epistemic_load 标注。
>
> **限制**:这一约束的可靠性取决于 B7 + B8 假设(员工标注的可靠性 + 员工愿意答这个问题)。这两个假设任何一个失效, 这条约束就降级为 "best-effort 默认值,可被员工显式 override"。

- **v4.1 新增澄清**:"自动化"在本约束中专指"系统替员工执行 business_action"。**系统在合适时机给出 reminder 不构成自动化**,这是 reminder 段存在的理由

### C3b. 可降级 / 可退出

- 任何时候员工都能把 deployment_mode 从 team 降级到 personal
- 降级后,系统的所有过往数据归员工本地,雇主无访问权
- **限制**:这是流程承诺,不是技术约束。可靠性取决于部署方诚信

---

# Part D — 系统架构

## 4.0 Skill Harvester 与 RPA 的关系(★ v4.1 新增,从原 Part A5 移入)

(回应 v3 review 第 4 条 — 假二分修正)

Skill Harvester 和 RPA 的差别**不在数据源**,在**目标表示**。

- **数据源**:两者都使用员工屏幕事件流。Skill Harvester 没有放弃 event trace,event trace 是 L1/L2 的核心输入,也是 L4.5 consistency check 的对照基准
- **目标表示**:RPA 把 event trace 直接编译成可重放脚本(目标是 trace 自身);Skill Harvester 把 event trace 用作 production hypothesis 的证据来源,目标表示是带类型条件的可读规则

**事件流贯穿全程,不是被淘汰的低级数据**。设计上的反思:v3/v4 文档曾把 "我们不是 RPA" 讲成 "我们不要 event recording",这是假二分,v4.1 在此正面修正。

## 4.1 七层架构总览

```
┌─────────────────────────────────────────────────┐
│  L5    Skill Compiler                           │
│        verification × epistemic 双轴矩阵输出  ★ │
├─────────────────────────────────────────────────┤
│  L4.5  Consistency Checker            ★ v4.1 改 │
│        replay LOO, 单向过滤(只能拒绝, 不能证明) │
├─────────────────────────────────────────────────┤
│  L4    Production Inducer                       │
│        输出 ProductionHypothesis                 │
│        conditions = trigger / decision 两段  ★  │
├─────────────────────────────────────────────────┤
│  L3    Dialogue Engine                          │
│        step 0: goal 分类                        │
│        step 1: immediate 一句话快问             │
│        step 2: deferred 对比追问                │
│        step 3: epistemic_load 标注 (voluntary) ★│
├─────────────────────────────────────────────────┤
│  L2    Episode Builder                          │
├─────────────────────────────────────────────────┤
│  L1    Sparse Sensor (sensor A + sensor B)      │
├─────────────────────────────────────────────────┤
│  L0    Task Catalog (动态生长)                  │
└─────────────────────────────────────────────────┘
```

**横切层**:
- §10 Deployment Manifest Gate(v4.1 加 override 流程)
- §11 Failure Modes 表(v4.1 加 LOO 小样本退化条目)

## 4.2 L0 / L1 / L2(沿用 v3/v4)

详见 [skill-harvester-design-v3.md §4.2-4.4](./skill-harvester-design-v3.md)。

## 4.3 L3 — Dialogue Engine(v4.1 修订:step 3 voluntary)

L3 的三时延档(immediate / close-window / deferred)沿用 v4 §4.5.1。

**v4.1 关键修订**:L3 step 3 (epistemic_load 标注) 从 mandatory 改为 **voluntary**。

具体规则:

1. step 3 与 step 2 **同时呈现**,不是追加在 step 2 之后
2. 员工可以**只回答 step 2,跳过 step 3**
3. 跳过的 episode 的 epistemic_load 字段为 `unlabeled`
4. L4 在归纳时遇到 unlabeled episode,不强制要求归类,产出的 hypothesis 标记为 `epistemic_load: unknown`
5. L5 编译时,`unknown` 的规则**默认进 hypothesis 段**(保守策略),由员工审阅时决定是否手动标记

**为什么这么改**:v4.1 self-review P0 第 2 条指出 step 3 是无条件追加问题,违反 v4 自家的 hard rule "永远不强制打断"。修复后 step 3 不再威胁 hard rule,代价是引入 unlabeled 状态。

## 4.4 ★ L4.5 — Consistency Checker(v4.1 重写)

**v4 原名**:Hypothesis Validator
**v4.1 改名**:Consistency Checker

这一改不是修辞,是**本质重定位**。v4 self-review P0 第 1 条指出:replay test 的 ground truth 鸡生蛋问题(v4-open-questions §1)是认识论问题不是工程问题,这意味着 replay test 不能宣称为"假设检验"。它只能做更弱但成立的事:**找出内部一致性低的规则**。

### L4.5 在 v4.1 的角色

- **能做的**:找出"它解释了训练 episode 但解释不了同 task 内未见过的 episode"的规则。这种规则更可能是过拟合或合理化产物
- **不能做的**:证明通过 replay 的规则是"真规则"。一条规则通过 replay 只意味着它**至少自洽**,不意味着它**是对的**

### Replay LOO 流程

```
输入:
  - 一条 production hypothesis H
  - 同一 task_id 下的 N 条 reviewed episodes (N ≥ 9 才启用 LOO)

步骤:
  1. 对 N 条 episode 中的每一条 e_i:
     a. 把 e_i 之外的 N-1 条作为"训练集"重新归纳 H'
     b. 用 H' 在 e_i 上做 trigger condition 匹配
     c. 如果匹配, 看 H' 预测的 action 和 e_i 实际 action 是否一致
  2. consistency_score = 一致次数 / 触发次数

输出:
  - consistency_score: 0.0 - 1.0
  - flag: ok | low_consistency | insufficient_sample
```

### 三个分支(v4.1 形式化)

1. **N < 9**(insufficient_sample):L4.5 **不评分**。所有 hypothesis 进 L5 的 hypothesis 段(不进 verified 段),等到 N ≥ 9 才启用评分
2. **N ≥ 9 且 consistency_score ≥ 0.7**(ok):hypothesis 进入 §4.4.1 描述的下一步
3. **N ≥ 9 且 consistency_score < 0.7**(low_consistency):反向触发 §4.4.1 的 L3 追问循环

**v4.1 P0 第 3 条修复**:N=5 时 LOO 只有 6 个离散值,A7 区分度阈值 ≥ 0.3 几乎不可能稳定达到 → 明确写出"N < 9 时 L4.5 不评分,退化为透明层"。这是把 v4 隐藏的崩溃路径变成显式的失败模式。

### 4.4.1 L4.5 → L3 反向闭环(★ v4.1 新增节)

低 consistency 的 hypothesis 不直接拒绝,而是**反向触发 L3 的针对性追问**。整个闭环是一个有限状态机:

```
[state: hypothesis_low_consistency]
  ↓ 反向追问
  L3 (针对性问题 — 见下表)
  ↓ 员工回答
[state: hypothesis_revised]
  ↓ L4 重新归纳 (使用追加的 dialogue)
  ↓ L4.5 重新跑 LOO
  ↓
  ├─ ok          → [state: verified]
  ├─ 仍 low      → loop_count++
  │                ├─ loop_count < MAX_LOOPS  → [state: hypothesis_low_consistency]
  │                └─ loop_count >= MAX_LOOPS → [state: tacit_floor_reached]
  └─ insufficient_sample → [state: hypothesis] (透明态)
```

#### MAX_LOOPS 的取值

**v4.1 P1 第 4 条修复**:v4 写"最多 3 轮"没有依据。v4.1 改为:

> MAX_LOOPS 是配置参数,默认 3。**Phase 0 假设 A9(v4.1 新增)负责标定**这个数字 — 在真实数据上,replay accuracy 在第几轮迭代后稳定。
>
> 在 A9 的数据出来之前,3 是一个**保守占位值**,理由:任何超过 3 轮的对话循环对员工来说都是骚扰,3 轮是 reminder 的认知极限。

#### 反向追问的问题生成

| L4.5 检测到的不一致类型 | L3 追问模板 |
|---|---|
| 同 task 但 trigger 没匹配上 | "ep_xxx 看起来和这条规则的情况很像,但你那次没按规则做。你那次和别的不同在哪?" |
| trigger 匹配但 action 预测错了 | "你这条规则在 ep_xxx 上预测你会 X,但你实际做了 Y。这两次是什么不一样?" |
| 同 trigger 在不同 episode 走不同 action | "ep_xxx 和 ep_yyy 看起来一样,但你处理得不同。能说说这两次的差别吗?" |

追问由 LLM 生成,**问题模板由本表决定**(不是 LLM 自由发挥),保证追问聚焦于不一致点而不是漫游。

#### 追问回答的合并方式

员工对反向追问的回答**追加到原 episode 的 dialogue 字段**(不是替换),保留对话历史。L4 重新归纳时把追加的 dialogue 一起喂给 LLM。

#### tacit_floor_reached 的处理

进入此状态后:
- 该规则**永久标记**为 tacit floor,不再尝试归纳
- 但**冷却期 90 天后**,如果该 task 又积累了 10+ 条新 episode,系统会**重新尝试一次**(因为新 episode 可能改变归纳基础)
- 重新尝试仍失败 → 进入永久 frozen 状态,需要员工显式 unfreeze

## 4.5 L4 — Production Inducer(v4.1 修订:trigger / decision 拆分)

### 输出类型

L4 的输出叫 **ProductionHypothesis**(沿用 v4),不是 Production。

### conditions 的 trigger / decision 拆分(★ v4.1 P1 第 5 条修复)

**v4 原 schema**(observable / declared / organizational / exception_only 4 子类):
- 硬约束"必须至少有 1 个 observable" 在真实业务规则上扭曲了规则结构
- 4 子类边界不清(同一条件可以归多类)

**v4.1 schema**:把 conditions 拆成两段,**先按角色分**,再在每段内按可观测性标注。

```yaml
conditions:
  trigger:                    # 决定规则何时被尝试匹配
    - field: active_app
      op: equals
      value: ERP
      observable: true
      source: window_focus
    - field: active_window_template
      op: equals
      value: "Refund Detail #N"
      observable: true
      source: window_title

  decision:                   # 决定 business_action 的判断条件
    - field: order_amount
      op: less_than
      value: 50
      unit: EUR
      observable: true
      source: erp_dom
    - text: "我个人偏好熟客优先"
      observable: false
      kind: declared
      source_dialogue: ep_20260408_003
    - text: "<50EUR 不需要主管复核"
      observable: false
      kind: organizational
      source_doc: refund_policy_v3.2.pdf#section-4
```

### 硬约束(v4.1 修订)

1. **trigger 段必须至少有 1 个 `observable: true` 条件**,否则规则不可匹配 → reject
2. decision 段可以是 observable / declared / organizational 的任意混合,**没有"必须至少 1 个 observable"约束** — 因为很多真实业务规则的判断条件都是非可观测的,强行要求会扭曲规则结构
3. 总条件数(trigger + decision)≤ 5(MDL 上限)
4. declared / organizational 条件必须有 source(`source_dialogue` 或 `source_doc`)→ 否则 reject

### 这一修订解决的问题

v4 self-review P1 第 5 条指出:很多真实业务规则的 IF 是 "observable trigger + declared/organizational decision" 的组合,v4 的"必须 ≥1 个 observable"硬约束会强迫 LLM 把判断条件归类为 observable,扭曲规则结构。

v4.1 把 observability 从"分类标签"改为"标注属性",并把硬约束限制在 trigger 段内 — 这样既保证规则可被 trigger(可证伪),又允许 decision 段忠实反映真实判断结构。

## 4.6 ★ L5 — Skill Compiler(v4.1 修订:二维矩阵输出)

### 二维分类

**v4 原设计**:三段输出(verified / hypothesis / reminder)— 但这把两个独立维度耦合成一段:

- 维度 1:**verification status**(规则的认识论可信度)— 来自 L4.5 consistency check
- 维度 2:**epistemic load**(规则的伦理可执行性)— 来自 L3 step 3 标注

**v4 的耦合错误**:epistemic_load: high 直接强制进 reminder 段,即使 L4.5 通过。这导致一条 "我们知道是对的,但我们故意不自动化" 的规则被混进 "还没验证好的" 段里,丢失了重要的语义区分。

**v4.1 二维矩阵**:

|                  | verification: ok | verification: low | verification: insufficient |
|---|---|---|---|
| epistemic: low   | **verified + auto** | hypothesis (LLM 软提示) | hypothesis (透明态) |
| epistemic: medium | verified + auto + ⚠ | hypothesis + ⚠ | hypothesis + ⚠ |
| epistemic: high  | **verified-but-reminder-only** | hypothesis-reminder | hypothesis-reminder |
| epistemic: unknown | hypothesis (待标注) | hypothesis (待标注) | hypothesis (透明态) |

### SKILL.md 输出格式

```markdown
---
name: refund_handling
description: 处理客户退款工单的决策规则
target: llm_agent_prior
verified_count: 3       # epistemic ≠ high 且 verification ok
verified_reminder_count: 1  # ★ v4.1 新增 (epistemic high 但 verification ok)
hypothesis_count: 2
unlabeled_count: 1
---

## 业务规则 — 已验证, 自动执行 (verified + auto)
### Rule 1: 小额可信客户自动批准
[verification: ok | epistemic: low | consistency_score: 0.92]
...

## 业务规则 — 已验证, 不自动执行 (verified-but-reminder-only)  ★ v4.1 新增段
### Rule 2: 大额退款审核前先看客户对话历史
[verification: ok | epistemic: high | consistency_score: 0.88]
> ⓘ 这条规则我们认为是对的, 但你在 L3 标注里说过这一步是你抓异常的关键时刻。
> 系统不会替你做这件事, 只会在合适时机提醒你。
> 如果你想让系统自动执行, 把这条 epistemic_load 改为 medium 或 low。
...

## 业务规则 — 候选假设 (hypothesis)
### Hypothesis A: ...
[verification: low | epistemic: medium]
> ⚠ 这条规则在历史数据上不一致 (consistency_score=0.55), 仅供参考。
...

## 业务规则 — 待标注 (unlabeled)
### Hypothesis B: ...
[verification: ok | epistemic: unknown]
> 你还没标注这条规则的 epistemic_load。请回 L3 step 3 完成标注。
...

## 来源审计
...
```

**v4.1 关键变化**:新增 `verified-but-reminder-only` 段,**保留"我们知道它是对的"的语义**,同时尊重员工标注的"不要自动执行"。这是 v4 self-review P1 第 6 条修复。

### epistemic_load 在 reminder 段里的意义

reminder 段不是"没验证好",是"**故意不自动化**"。Agent 看到 reminder 段的规则时:

- 不自动执行 business_action
- 在合适时机(由触发条件判断)给员工一个提醒:"按你以前的标准,这种情况你会做 X。要不要现在做?"
- 员工的回答(做 / 不做 / 改 X)不被回写为"L4.5 反向触发数据" — 因为这不是不一致,是有意识的 case-by-case 判断

---

# Part E — 路线图与验证

## 6.1 七层 + 假设的对应(v4.1 修订)

| 层 | 对应假设 | v4.1 变化 |
|---|---|---|
| L0 | A1 / **B0** | v4.1 加 B0 |
| L1 sensor A | A2 上游 | — |
| L1 sensor B | A6 / B5 | — |
| L2 | (隐含) | — |
| L3 step 0 | A2 / B2 | — |
| L3 step 1 | A3a / B3 | — |
| L3 step 2 | A3b / B4 | — |
| L3 step 3 | A8 / B7 + **A8b / B8** | v4.1 加 voluntary 假设 |
| L4 | A4 / B1 | conditions schema 改 |
| **L4.5** | A7 / B6 + **A9** | v4.1 加迭代收敛假设 |
| L5 / Agent | A5 | — |

## 6.2 Phase 0 假设(v4.1 修订到 11 个)

### 沿用 v4 的 9 个

A1 / A2 / A3a / A3b / A4 / A5 / A6 / A7 / A8 — 详见 [v4 §6.2](./skill-harvester-design-v4.md#62-phase-0-扩充v4) 和 [phase0/README.md](./phase0/README.md)。

**A7 在 v4.1 中降级**:
- v4 阈值:三种规则的 replay accuracy 区分度 ≥ 0.3
- **v4.1 阈值**:N ≥ 9 时,真规则 consistency_score 严格高于合理化规则(任意大小的差距);N < 9 时 A7 自动 SKIP(L4.5 退化为透明层)
- **理由**:v4 self-review P0 第 3 条指出 N=5 时 LOO 只有 6 个离散值,0.3 区分度不可能稳定达到

### v4.1 新增的 2 个

#### A8b — L3 step 3 自愿标注率

**问题**:即使 step 3 改为 voluntary,员工是否真的愿意答?如果自愿率太低,B7 假设也无意义(没人答就没数据)。

**通过标准**:reviewed episode 中的 step 3 自愿标注率 ≥ 30%(比 A3a 的 10% 高,因为 step 3 比 immediate 一句话快问的认知负担低 — 它是与 step 2 同时呈现的)

**不通过的备选方案**:把 step 3 从 "voluntary inline" 改为 "weekly batch" — 一周一次专门让员工补标注,不放在每条 episode 的 review 流程里

#### A9 — L4↔L4.5 迭代收敛性

**问题**:MAX_LOOPS = 3 是拍脑袋数字。在真实数据上,replay accuracy 在第几轮迭代后稳定?

**做法**:
1. 从 A7 的数据里挑出 5 条进入"反向追问循环"的 hypothesis
2. 跑 5 轮 L3↔L4↔L4.5(超过默认的 3),记录每轮的 consistency_score
3. 看 consistency_score 在第几轮趋于稳定

**通过标准**:
- ≥ 60% 的 hypothesis 在 ≤ 3 轮内 consistency_score 稳定(变化 < 0.1)
- 没有 hypothesis 在 5 轮后还在显著震荡

**如果通过**:MAX_LOOPS = 3 是合理默认
**如果不通过(收敛太慢)**:MAX_LOOPS 上调,或者改 L4.5 算法
**如果不通过(收敛但不向上)**:tacit floor 是真实存在的常态,§11 失败模式表的 "Tacit floor reached" 触发频率会比预期高

## 6.3 Phase 1(v4.1)— 闭环原型 + L4.5 stub

**v4.1 修订**:Phase 1 的 P0 模块清单(对应 [CHANGELOG v4 章节的工作包](./CHANGELOG.md#v4--2026-04-08-design-only-no-code-yet)):

| 模块 | v4.1 变化 |
|---|---|
| `models.py` | conditions 改为 trigger / decision 两段;新增 `verified-but-reminder-only` 状态;新增 `unlabeled` 状态 |
| `validator.py` | **改名建议** `consistency_checker.py`;实现 N < 9 透明态;实现 §4.4.1 反向闭环状态机 |
| `inducer.py` | 输出新 conditions schema;LLM prompt 加 trigger / decision 区分 |
| `compiler.py` | 二维矩阵 4 段输出 |
| `dialogue.py` | step 3 改为 voluntary |
| `phase0/data.example.yaml` | 加 A8b / A9 段 |
| `phase0/verify.py` | 加 A8b / A9 scorer |
| `cli.py` | 启动时调 deployment gate(含 §10 override 路径) |
| `deployment.py` | **新增 override 流程**(见 §10) |

### Phase 1 验收(v4.1 修订)

- v3 的端到端 A/B +20pp(不变)
- A7 真规则 consistency 严格高于合理化(N ≥ 9 时)
- A8 IRR ≥ 0.6 + A8b 自愿率 ≥ 30%
- A9 收敛性 ≥ 60%
- deployment manifest gate 单元测试通过(故意污染 → 拒绝启动 + override 路径走通)

## 6.4 Where to start(★ v4.1 新增)

读完 v4.1 文档后,实际的工作起点不是写代码,是:

1. **读 [essence.md](./essence.md)** — 项目不动点
2. **读 [phase0/README.md](./phase0/README.md)** — 7 天可行性证伪流程
3. **跑一轮 Phase 0**(11 个假设)
4. 如果 Phase 0 全部 PASS → 进 Phase 1 工程(本文档 §6.3)
5. 如果 Phase 0 有 FAIL → 不要进 Phase 1,在 CHANGELOG 加 v4.2 章节记录 pivot

---

# Part F — 失败模式

## 11. Failure Modes(v4.1 修订:加 LOO 小样本 + non-goals 映射)

| 失败模式 | 可观测信号 | 系统行为 | 对应 non-goal |
|---|---|---|---|
| **Insufficient sample** ★v4.1 | 某 task 的 reviewed episode N < 9 | L4.5 透明态:所有 hypothesis 进 hypothesis 段不评分 | — |
| **Tacit floor reached** | 某 task hypothesis 连续 MAX_LOOPS 轮迭代后 consistency_score 仍 < 0.7 | 标记 frozen,90 天 + 新数据后单次重试 | non-goal: 模糊判断/案例类比 |
| **Dialogue collapse** | 同一员工连续 3 次 L3 对话 info_score < 2 | 暂停 L3 自动追问 7 天,通知员工 | — |
| **Rule representation insufficient** | LLM 连续 3 次输出 "cannot express as IF-THEN" 或 trigger 段无 observable | 转为自然语言注释,挂在 SKILL.md 的 informal notes 段 | non-goal: 多模态直觉 |
| **Human-in-the-loop required** | epistemic_load: high 或 task 命中高风险标签 | 永远不进 verified-auto,只进 verified-but-reminder-only 或 hypothesis-reminder | non-goal: epistemic function |
| **Subjectivity erosion** ★v4.1 改 | 月度 self-checkin 答 "用了系统后我对工作的掌控感下降" | 触发 deployment review;**这是软指标,需要 cli.py 的 monthly_checkin 子命令实现(v4.1 新增 to-do)** | — |
| **Manifest violation** | manifest 关键字段违反规范前提 | 进入 §10 override 流程,默认拒绝启动 | — |
| **Drift detection** | verified rule 在生产中被 Agent 调用后连续 N 次失败 | 降级回 hypothesis,反向触发 L3 追问 | non-goal: 强实时控制 |
| **Step 3 starvation** ★v4.1 | A8b 自愿率持续 < 30% | step 3 改为 weekly batch 模式;触发 B8 假设的 fallback 路径 | — |

**v4.1 P2 第 6 条修复**:Subjectivity erosion 现在明确写出"需要 cli.py 的 monthly_checkin 子命令" — 这是 Phase 1 的具体工作项,不再是悬空软指标。

---

# §10 — Deployment Manifest Gate(v4.1 加 override 流程)

## 10.1 manifest 文件

```yaml
# ~/.skill-harvester/deployment_mode.yaml
deployment_mode: personal       # personal | team
guarantees:
  visibility_owner: employee
  edit_owner: employee
  delete_owner: employee
  portability: true
  sharing_consent: explicit
  use_for_evaluation: false
  use_for_monitoring: false
```

## 10.2 启动检查

CLI 启动时:
1. 加载 manifest
2. 与 Part C C-enforced 的默认值对比
3. **任何字段被改成违反默认的值** → 进入 §10.3 override 流程

## 10.3 ★ v4.1 新增:override 流程

(回应 self-review P1 第 9 条 — v4 没说怎么 override)

### override 路径

如果部署确实需要 override(例如团队模式下需要 use_for_monitoring=true),员工必须:

1. 在 CLI 上显式确认 override:
   ```
   skill-harvester start --override-manifest \
     --override-fields use_for_monitoring \
     --reason "team trial, monitoring opt-in"
   ```
2. 系统**强制等待 5 秒**(防止误操作)并打印将要被 override 的字段
3. 写入 audit log:`~/.skill-harvester/audit/override.log`(只追加,不删除)
4. 系统启动后,在每次 CLI 输出顶部显示**红色横幅**:`⚠ DEGRADED ETHICAL MODE: use_for_monitoring=true (since YYYY-MM-DD)`
5. 员工可以随时回到默认:`skill-harvester reset-manifest`(无需 reason)

### 谁能 override

- **personal 模式**:只有员工本人(本机操作即视为本人)
- **team 模式**:员工本人 + 一个外部审核签名(签名机制留给 Phase 3,Phase 1/2 阶段团队模式禁用)

### override 不能做的事

以下字段**永远不能 override**:

- `delete_owner: employee`(否则系统失去可删除性,违反 essence)
- `portability: true`(否则数据被锁定,违反 essence)

如果配置文件试图 override 这两项,CLI **硬拒绝启动**,无 override 路径。

---

# 附录 A — v4 → v4.1 修订对照(self-review 9 条)

| # | 严重 | 问题 | 修订位置 | 措施 |
|---|---|---|---|---|
| P0-1 | L4.5 ground truth 矛盾 | §0.3 / §4.4 / Part B6 | 改名 Consistency Checker;B6 措辞降级为单向过滤;承认 review 第 3 条只是部分回应 |
| P0-2 | L3 step 3 违反 hard rule | §4.3 / Part B8 / §6.2 | step 3 改 voluntary;新增 B8 / A8b |
| P0-3 | LOO 小样本崩溃 | §4.4 / §6.2 / §11 | 形式化 N < 9 透明态;A7 阈值降级;§11 加 Insufficient sample 条目 |
| P1-4 | MAX_LOOPS 没依据 | §4.4.1 / §6.2 | 新增 A9 假设;3 轮作为 Phase 0 后校准的占位 |
| P1-5 | conditions 边界不清 | §4.5 | trigger / decision 拆分;observable 从分类标签改为标注属性 |
| P1-6 | epistemic × verification 耦合 | §4.6 | 二维矩阵 4 段输出;新增 verified-but-reminder-only 段 |
| P1-7 | C2 措辞冲突 | Part C-best-effort | C2 从 enforced 降到 best-effort;明确 "automation ≠ reminder" |
| P2-8 | Subjectivity erosion 不可执行 | §11 | 明确写出需要 monthly_checkin 子命令 |
| P2-9 | manifest 没 override 路径 | §10.3 | 新增 override 流程 + 永久不可 override 字段 |

**未在 v4.1 修的(留给 v5)**:
- v4 self-review S1/S2/S3/S4(文档结构问题) — 不影响正确性,留给后续
- v4-open-questions §1 ground truth 鸡生蛋 — 认识论问题,认 L4.5 改名为部分缓解
- v4-open-questions §3 多员工合并 — 范围外
- v4-open-questions §4 UI 漂移检测 — 留给 Phase 3
- v4-open-questions §5 manifest 多机器同步 — 留给 Phase 3

---

# 附录 B — 仍未在 v4.1 内闭合的问题

见 [v4-open-questions.md](./v4-open-questions.md)(v4.1 同步更新,删除原第 6 条元问题,新增 v4.1 自检发现的问题)。

主要包括:
1. Replay test 的 ground truth 鸡生蛋问题(v4.1 用"改名 + 措辞降级"部分缓解,根本未解)
2. epistemic_load 的主观漂移(v4.1 引入 unknown/unlabeled 状态部分缓解)
3. 多员工版本的规则合并裁决
4. UI 漂移检测的反向触发链路
5. deployment manifest 在多机器同步场景下的一致性
6. **【v4.1 新增】** essence.md 与 v4.1 design 的措辞断层(essence 说"在角落亮一下",v4.1 说"自愿触发的红点" — 一致但风格不同,跨文档跳转有断层)

---

# 文档半衰期声明(★ v4.1 新增)

> **本文档每 6 个月或 Phase 0 / Phase 1 数据出来后必须 review。**
>
> v4.1 是技术参考文档,它的修订门槛比 essence.md 低 — 任何 Phase 0 数据 / 任何工程实践经验 / 任何新的 review 都可能触发 v4.2 / v5。
>
> 但 essence.md 没有半衰期 — 它的修订门槛是"项目根本立场变化"。

---

*v4.1 修订基于 v4 + 一份自检报告(P0×3 / P1×3 / P2×3)。完整 self-review 内容和逐条修复见本文档附录 A 和 [CHANGELOG.md](./CHANGELOG.md) v4.1 章节。*
