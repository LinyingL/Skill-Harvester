# Skill Harvester — 项目设计文档 v4

> **⚠ v4 已被 [v4.1](./skill-harvester-design-v4.1.md) 取代。** v4.1 修复了 v4 自检发现的 9 个问题(L4.5 改名 Consistency Checker、conditions trigger/decision 拆分、L5 二维矩阵输出、deployment manifest override 流程等)。除非你在追溯 v3 → v4 的演化过程,否则请直接读 v4.1。
>
> **这是技术参考文档。如果你想知道这个项目"是什么 / 为什么 / 怎么做",请先读 [essence.md](./essence.md) — 那才是项目的不动点。本文档只解释"技术上具体怎么实现"。**
>
> **v4 修订说明**:这一版不是对 v3 的局部补丁,是对**论证结构本身**的重构。
>
> v3 的所有技术架构(六层 + 两条触发线 + 三时延对话)在 v4 里依然成立。但 v3 把"描述性事实"、"设计假说"、"规范立场"三类命题混在一篇连贯叙事里,看起来很顺,实际上隐藏了五座没被论证的桥:**可表达性 / 可形式化性 / 可验证性 / 可迁移性 / 控制权归属**。
>
> v4 把这五座桥逐一显式化,代价是文档结构必须重组,新增一层 **L4.5: Hypothesis Validator**,新增一份代码级伦理 gate(deployment manifest),并把 conditions schema 从 `list[str]` 升级为按可观测性分层的类型化结构。
>
> v4 的出发点来自一份十条逻辑 review(完整记录在 [CHANGELOG.md](./CHANGELOG.md) v4 章节)。这一份 review 是迄今为止最严肃的一次,因为它打的不是组件,是论证结构。
>
> **v4 文档结构**:按命题类型分三段(Part A 描述 / Part B 设计 / Part C 规范),不再混在一起。每一段的证明负担、检验方式、修订门槛都不同,必须分开处理。
>
> v3 文档保留在仓库里作为对照:[skill-harvester-design-v3.md](./skill-harvester-design-v3.md)。

---

## 0. 核心信念(v4 重写)

### 0.1 Skill 的收窄定义

> **Skill 是可重复实践能力中,那些能够被诱导表达(elicited)、抽象(abstracted)、形式化(formalized)、且委托执行(delegated)的部分。**

v3 写的 "Skill 是显性知识压缩成自动化程序" 是一个**有害的简化**。它把 Skill Harvester 的工作描述成 "ACT-R compilation 反向跑",但 ACT-R 框架本身并没有定义 procedural → declarative 的反向通道 —— Anderson 自己承认这是单向的。v3 用了一个不严格的隐喻当方法论,把最难的步骤偷偷跳过去。

v4 用三个独立动词代替这个隐喻:

```
tacit competence  ──elicit──>  partial articulation
                  ──abstract──> rule hypothesis
                  ──formalize──> typed production
                  ──delegate──> SKILL.md (LLM-Agent prior)
```

每一步都有自己的失败模式(见 §11),都不是自动发生的。Skill Harvester 的工作就是把这四个动词分别落到 L3 / L4 / L4.5 / L5 上。

### 0.2 SKILL.md 是什么,不是什么

**是什么**:

- 给下游 LLM Agent 的**上下文先验**(prior),不是给传统执行引擎的硬规则
- 技能的**部分表示**(partial representation),只覆盖那些能被形式化的部分
- **可审计、可编辑、可删除**的人类可读 Markdown,不是黑盒模型权重

**不是什么**(non-goals):

- ❌ Skill 的完备表示 —— production rules **不假装能穷尽**模糊判断、情境权重、案例类比、非单调推理。这一类由 LLM Agent 的语言理解兜底,不由 Skill Harvester 兜底
- ❌ 高度依赖多模态直觉的判断(语气微表情、视觉模式识别、审美)
- ❌ 强实时控制循环(交易、操作系统调度)
- ❌ 需要精确执行而非判断(财务对账)
- ❌ **承担 epistemic function 的重复动作**(风险确认 / 责任 checkpoint / 异常感知 / 早期发现)—— 这一类**不应被自动化,只应被显性化**(见 §6.5)
- ❌ 极度个性化的一次性创作(写诗)

**关键澄清**(回应 v3 review 第 2 条):
> "production rules 不能穷尽 Knowing How" 这一论断我们**完全接受**。Skill Harvester 的产物是**容易被形式化的那部分技能**,加上 LLM Agent 在执行时的语言理解能力,共同覆盖一个完整 task。两者是分工关系,不是替代关系。"系统因为 IF-THEN 表达力不够而崩溃" 这一类质疑应由 LLM Agent 那一层回答,不由 Skill Harvester 回答。

### 0.3 三步分解图(elicit → abstract → formalize → delegate)

```
[L3 step 2] elicit       — 反事实对话, 把 tacit 变成 partial articulation
[L4]        abstract     — 跨 episode 抽出候选规则
[L4.5]      validate     — replay test, 把 hypothesis 变成 verified rule  ★v4 新增
[L4]/[L5]   formalize    — 用 typed conditions schema 写出可证伪的 production
[L5]        delegate     — 编译成 SKILL.md, 进入 Agent 调用入口
```

每一步的失败模式参见 §11。

### 0.4 规范前提(non-negotiable)

> **自动化的收益、控制权与节省时间应主要归属于执行者本人。在这个前提不成立的部署里,Skill Harvester 不应被使用。**

这不是设计取舍,是产品的伦理底线。它的可执行实现是 §10 的 deployment manifest。

v3 把 README 里那句 "Humanity is an end, never merely a means"(Kant) 当作宣言,v4 把它落到代码层面 —— 启动时检查 manifest,违反规范前提的部署 → CLI 拒绝启动。

---

# Part A — 描述性命题(Descriptive)

> 这一段是 v4 立论的"已知事实",每一条都有外部证据。读者**不需要相信我们**,只需要去查参考文献。
>
> 描述性命题的修订门槛:出现新的实证证据。

## A1. 人类技能有大量 tacit 与 procedural 成分

- **证据**:Polanyi 1966 *The Tacit Dimension* — "We know more than we can tell"
- **证据**:Anderson 1983/1993 ACT-R — declarative/procedural 双系统;procedural 一旦下沉到 sub-symbolic activation 层就**不能**被 declarative 自省
- **证据**:Dreyfus & Dreyfus 1986 五阶段技能模型 — 专家阶段的判断是"识别即行动",不经过显式推理

**对设计的含义**:任何依赖"让专家描述自己怎么做"的方法,都会**系统性地丢掉**已经下沉到 procedural 层的那部分。这就是为什么 v4 必须有 L3(诱导表达层)和 L4.5(假设检验层)—— 仅靠员工自我报告是不够的。

## A2. 已压实的产生式没有 surprisal 信号

- **证据**:Klein RPD(Recognition-Primed Decision)模型 — 专家在熟悉情境下的决策是"模式匹配 → 直接行动",**没有停顿、没有比较**
- **证据**:ACT-R 三阶段 — autonomous 阶段的产生式触发延迟接近 0,意识访问不到

**对设计的含义**:仅靠 surprisal 触发器(L1 sensor A)会**系统性漏掉**最有价值的那一类产生式。这就是 v3 引入 L1 sensor B(频率累加器)的依据。

## A3. 事后回忆质量随时间快速衰减

- **证据**:Ericsson & Simon 1980/1993 *Protocol Analysis* — concurrent verbalization 和 retrospective verbalization 的可信度差距是数量级的
- **证据**:Nisbett & Wilson 1977 *Telling more than we can know* — 人对自己行为原因的回溯解释**经常是构造的**,与真实因果机制脱钩
- **证据**:遗忘曲线 (Ebbinghaus) — 情景记忆在小时级以内大幅衰减

**对设计的含义**:v3 的"下班前批处理对话"是错的。v4 把 L3 拆成三时延档(immediate / close-window / deferred),并且按追问类型分发 —— 瞬时记忆型问题必须 immediate,规律记忆型问题可以 deferred。

## A4. 自我报告 ≠ 真实驱动机制

- **证据**:同 A3 (Nisbett & Wilson)
- **证据**:Cognitive Task Analysis 文献(Crandall, Klein, Hoffman 2006)— elicited rules 必须经过 critical decision method 的反复对照才能近似真实机制

**对设计的含义**(★ 这是 v4 新增 L4.5 的依据):
对话拿到的不是"规则真理",只是"规则假设"。v3 直接把对话产出当成 production 写进 SKILL.md,这一步在逻辑上断裂。v4 必须新增**假设检验循环**:elicited → hypothesis → replay test → correct → confidence update。

## A5. event trace 与 rule discovery 不是对立关系

- **证据**:数据挖掘 / process mining 文献(van der Aalst 2016)— rule discovery 通常以 event log 为输入

**对设计的含义**(回应 v3 review 第 4 条):
v3 把"我们不是 RPA"讲成"我们不要 event recording",这是假二分。v4 修正:**event trace 是证据来源,production hypothesis 是目标表示**。L1/L2 的事件流贯穿全程,既被 L4 用来生成 hypothesis,也被 L4.5 用来 replay test。事件流不是被淘汰的低级数据。

---

# Part B — 设计假说(Design hypotheses, falsifiable)

> 这一段是 v4 的"赌注"。每一条都是可证伪的,对应 Phase 0 的一个验证项。
>
> 设计假说的修订门槛:Phase 0 / Phase 1 的实测数据。

## B1. 一部分 tacit knowledge 可通过对话 + 案例校正转为可执行表示

- **关键限定**:**一部分**,不是全部
- **不可证伪的强版本**:"所有 tacit knowledge 都能被 elicit" — v4 拒绝这个版本
- **可证伪的弱版本**:"在可观测条件占优的任务里,L3+L4+L4.5 流程能产出 replay 一致率 ≥ 阈值的规则" — Phase 0 假设 A4
- **验证方式**:Phase 0 假设 A4 + Phase 1 末尾端到端 A/B (A5)

## B2. LLM 在 L0 task catalog 约束下能做高置信度 goal 分类

- 验证方式:Phase 0 假设 A2

## B3. immediate 一句话快问能在不打扰前提下抓瞬时记忆

- 验证方式:Phase 0 假设 A3a

## B4. deferred 对比追问不依赖瞬时记忆

- 验证方式:Phase 0 假设 A3b

## B5. routine 频率累加器能找到已压实的 high-value 产生式

- 验证方式:Phase 0 假设 A6

## B6. **【v4 新增】replay test 能区分真规则和事后合理化**

- **核心命题**:把一条 elicited rule 拿去 replay 历史 episode,如果它对**未参与归纳**的 episode 也能预测出实际 action,那它更可能是真规则;如果只能拟合训练 episode,那它更可能是事后合理化
- **认识论依据**:这是经典的 train/test split,把 elicitation 从"故事生成"变成"假设检验"
- **风险**:很多 episode 没有"ground truth action"(因为正确动作本身就是被归纳的对象)— 这是个鸡生蛋问题,见 [v4-open-questions.md](./v4-open-questions.md) 第 1 条
- **验证方式**:Phase 0 新增假设 **A7**(见 §6.3)

## B7. **【v4 新增】员工能可靠地标注 epistemic_load**

- **核心命题**:对每条候选规则,员工能可靠回答"如果系统替你做这一步,你会不会失去对某种异常的早期发现能力?"
- **依据**:让员工自己判断哪些动作不该被自动化,这是把"epistemic function"概念形式化的最朴素方式
- **风险**:员工可能过度保守(全部标 high)或过度激进(全部标 low)— 需要测试两个员工在同一组规则上的标注 IRR(inter-rater reliability)
- **验证方式**:Phase 0 新增假设 **A8**(见 §6.3)

---

# Part C — 规范约束(Normative constraints, non-negotiable)

> 这一段不是论证,是底线。规范约束不能被 Phase 0 数据证伪 —— 数据再漂亮,违反规范约束的部署也不被支持。
>
> 规范约束的修订门槛:伦理论证 + 制度设计层面的讨论,不是工程数据。

## C1. 用户对自己 skill 的 5 项控制权

(回应 v3 review 第 7 条)

| 权利 | 含义 | 代码层实现 |
|---|---|---|
| **Visibility** | 谁能看到 skill 的内容 | `deployment_mode.yaml` 的 `visibility_owner` 字段 |
| **Edit** | 谁能修改 skill | `edit_owner` |
| **Delete** | 谁能删除 skill | `delete_owner` |
| **Portability** | skill 能否随员工迁移到新雇主 | `portability` |
| **Sharing consent** | 共享必须显式同意 | `sharing_consent: explicit` |

**默认值**:全部归 `employee`。任何字段被改成 `employer` → 系统在 §10 deployment gate 处给出 warning;`use_for_evaluation` / `use_for_monitoring` 被改成 `true` → CLI 拒绝启动。

## C2. epistemic function 不被自动化

(回应 v3 review 第 8 条)

> 承担 **epistemic function**(风险确认 / 责任 checkpoint / 异常感知 / 早期发现) 的重复动作 **不应被自动化,只应被显性化**。

**实现**:见 §6.5 — production hypothesis 带 `epistemic_load` 标签,`high` 的 hypothesis 不进入 SKILL.md 的 "automated execution" 段,只进入 "reminder" 段。

## C3. 默认不用于评价 / 监控 / 排名

- 默认 `use_for_evaluation: false`,`use_for_monitoring: false`
- 这两条改成 true 需要 explicit override 并触发 audit log

## C4. 部署模式可被员工随时降级

- 任何时候员工都能把 deployment_mode 从 `team` 降级到 `personal`
- 降级后,系统的所有过往数据归员工本地,雇主无访问权
- 这是"控制权归属"在时间维度上的延伸

---

# Part D — 系统架构(Technical Architecture)

> 这一段是把 Part B 的设计假说和 Part C 的规范约束落到具体组件上。
>
> v4 在 v3 六层架构基础上新增 **L4.5: Hypothesis Validator** 和 **conditions schema 类型化**。其他层基本沿用 v3,变化的部分会标注 [v4]。

## 4.1 七层架构总览

```
┌─────────────────────────────────────────────────┐
│  L5   Skill Compiler         → SKILL.md         │
│       intent / execution / reminder 三段        │  [v4 加 reminder]
├─────────────────────────────────────────────────┤
│  L4.5 Hypothesis Validator   → verified rules   │  ★ v4 新增
│       replay test, confidence update            │
├─────────────────────────────────────────────────┤
│  L4   Production Inducer     → rule HYPOTHESES  │  [v4 改名]
│       conditions: typed (observable / declared  │
│       / organizational / exception_only)        │  [v4 类型化]
├─────────────────────────────────────────────────┤
│  L3   Dialogue Engine                           │
│       step 0: goal classification               │
│       step 1: immediate 一句话快问              │
│       step 2: deferred 对比追问                 │
│       step 3: epistemic_load 标注 [v4]          │
├─────────────────────────────────────────────────┤
│  L2   Episode Builder        → 困难+流畅        │
├─────────────────────────────────────────────────┤
│  L1   Sparse Sensor                             │
│       sensor A: surprisal                       │
│       sensor B: routine frequency               │
│       buffer:   recent_metadata 15min           │
├─────────────────────────────────────────────────┤
│  L0   Task Catalog (动态生长)                   │
└─────────────────────────────────────────────────┘
```

**v4 横切层**:
- **§10 Deployment Manifest Gate** — CLI 启动时检查 C1/C2/C3,违反规范前提则拒绝启动
- **§11 Failure Modes** — 列出系统应该如何"宣告自己失败"

## 4.2 L0 / L1 / L2 / L3(v4 沿用 v3,微调)

L0 / L1 / L2 完全沿用 v3,见 [v3 §4.2 / §4.3 / §4.4](./skill-harvester-design-v3.md)。

L3 在 v3 的三时延档基础上新增 **step 3: epistemic_load 标注**:
- 对每个 reviewed episode,在 deferred 阶段问员工一个额外问题:
  > "如果系统以后看到这种情况自动帮你做这件事,你会不会担心错过什么异常?"
  > A. 不会, 这就是机械操作 (epistemic_load: low)
  > B. 有时会, 我有时候也是靠做这一步发现问题的 (epistemic_load: medium)
  > C. 会, 这一步是我抓异常的关键时刻 (epistemic_load: high)
- 这个标注会传给 L4 / L4.5 / L5,决定产物落进 SKILL.md 的哪一段

## 4.3 L4 — Production Inducer(v4 类型化)

**v4 关键变化 1**:输出叫 **production hypothesis**,不叫 production。命名上把"未验证"显式化。

**v4 关键变化 2**:`conditions` 字段从 `list[str]` 升级为类型化结构(回应 v3 review 第 5 条 — circumstances 没有形式边界):

```yaml
conditions:
  observable:        # 可从屏幕/API/事件流直接读到
    - field: order_amount
      op: less_than
      value: 50
      unit: EUR
      source: erp_window_dom
    - field: customer_tenure_months
      op: greater_than
      value: 6
      source: erp_api

  declared:          # 员工声明的偏好/经验法则, 不能从屏幕读
    - text: "熟客优先"
      source_dialogue: ep_20260408_003

  organizational:    # 来自外部 SOP 文档
    - text: "<50EUR 不需要主管复核"
      source_doc: refund_policy_v3.2.pdf#section-4

  exception_only:    # 只在例外情况下匹配, 不能单独支撑规则
    - text: "客户邮件语气特别急"
      detection_hint: nlp_sentiment
```

**硬约束**(L4.5 在归纳后立即检查):

1. **必须至少有 1 个 `observable` 条件**,否则规则不可证伪 → reject
2. `exception_only` 条件不能单独支撑规则 → 必须挂在 observable 条件旁
3. `declared` / `organizational` 条件必须有 `source_dialogue` 或 `source_doc` → 否则 reject
4. 总条件数 ≤ 5(MDL 上限,防止"事后追加上下文"无限膨胀)— 回应 v3 review 第 5 条

**关键设计**:这个 schema 让"circumstances 无限开放"问题直接消失。每个条件都有类型、有来源、有可证伪边界。

## 4.4 ★ L4.5 — Hypothesis Validator(v4 新增)

**职责**:把 L4 的 hypothesis 从"故事"变成"已验证规则",通过 replay test。

**为什么需要这一层**:回应 v3 review 第 3 条 —— 对话拿到的是自我报告,自我报告可能是事后合理化。仅靠"另一名员工 endorse" 不能区分真规则和合理化故事。需要客观的 replay 验证。

### Replay test 流程

```
输入:
  - 一条 production hypothesis H
  - 同一个 task_id 下的 N 条 reviewed episodes
  - 其中 K 条参与了 H 的归纳 (training set), N-K 条没参与 (test set)

步骤:
  1. 对 test set 里的每一条 episode E:
     a. 抽取 E 的 observable 条件值
     b. 看 H 的 conditions 是否匹配
     c. 如果匹配, H 预测的 business_action 是什么
     d. 把预测和 E 实际发生的 action 对比
  2. 计算 test set 上的 hit rate = correct_predictions / total

输出:
  - test_replay_accuracy: 0.0 - 1.0
  - 如果 test_replay_accuracy >= 阈值 (默认 0.7) → 标记为 verified
  - 否则:
      - 把 H 的 confidence 降级
      - 把 H 加进 L3 的 "需要进一步追问" 队列, 触发针对性反事实问题
        ("你这条规则在 ep_xxx 上预测错了, 能解释为什么吗?")
      - 不进入 L5
```

### Replay test 的两个深层问题

**问题 1**:**没有 ground truth action 的鸡生蛋问题**
许多 episode 的"正确动作"本身就是被归纳的对象 —— 我们没有独立的 ground truth。
**v4 的回答**:在 Phase 1 假设员工的实际 action 就是 ground truth(后验合理性假设),这在多数业务场景下足够。极端情况(员工自己在历史 episode 上也犯过错)留给 [v4-open-questions.md](./v4-open-questions.md) 第 1 条。

**问题 2**:**train/test split 在 N=10 量级上很不稳定**
小样本下随机切分导致 test_replay_accuracy 方差很大。
**v4 的回答**:用 leave-one-out cross-validation 替代 train/test split,N 条 episode 每次留 1 条做 test,跑 N 次取平均。计算量大但 N 本来就小,可接受。

### 与 L3 的反向耦合

L4.5 拒绝一条 hypothesis 后,**反向触发 L3 的新一轮追问**。这是 v4 把"对话 → 规则"从单向流变成闭环的关键:

```
L3 → L4 → L4.5 → 通过 → L5
              ↓ 不通过
              L3 (针对性追问) → L4 (重新归纳) → L4.5 (再 test)
```

最多迭代 3 轮,3 轮后仍不通过 → 标记为 "tacit floor reached",停止对该规则的归纳尝试(见 §11)。

## 4.5 L5 — Skill Compiler(v4 三段输出)

v4 的 SKILL.md 输出分三段:

```markdown
---
name: refund_handling
description: 处理客户退款工单的决策规则
target: llm_agent_prior     # v3 加的, 强调不是硬规则
verified_rules: 5
hypothesis_rules: 2          # v4: 没通过 replay 但仍保留作为提示
reminder_rules: 1            # v4: 高 epistemic_load, 不自动执行
---

## 业务规则 — 已验证 (verified)
### Rule 1: 小额可信客户自动批准
[完整规则, 含 typed conditions 和 replay accuracy]

## 业务规则 — 候选假设 (hypothesis, replay 未通过)
### Hypothesis A: ...
> ⚠ 这条规则没有通过 replay test (acc=0.55), 仅供参考。

## 提醒清单 — 不自动执行 (high epistemic load)
### Reminder 1: 大额退款审核前先看客户对话历史
> 这一步不会被系统替你做。
> 系统只会在你打开退款详情时提醒你: "记得先看一下对话历史"。
> 理由: 你在 L3 对话里说过这一步是你抓异常的关键时刻。

## 来源审计
- Rule 1 基于 episodes [...] | replay acc 0.92 | typed conditions: 3 observable, 1 declared
- ...
```

**三段的语义**:
- **verified**:通过了 L4.5 replay test,Agent 可以自动执行
- **hypothesis**:对话产物,但 replay test 没通过 → 给 Agent 看,作为软提示,不自动执行
- **reminder**:epistemic_load: high → 系统**永远不会**替员工做,只会在合适时机提醒

---

# Part E — 路线图与验证

## 6.1 七层 + 七假设的对应

| 层 | 对应假设 | 失败信号 |
|---|---|---|
| L0 | A1 | 写不出动宾任务 |
| L1+L2 sensor A | (隐含 A2 上游) | 漏关键 episode |
| L1+L2 sensor B | A6 | 频率检测找不到高频流畅模式 |
| L3 step 0 | A2 | LLM 分类准确率不够 |
| L3 step 1 | A3a | 自愿触发率太低 |
| L3 step 2 | A3b | 对话信息量太低 |
| L3 step 3 | **A8 [v4 新增]** | epistemic_load 标注 IRR < 0.6 |
| L4 | A4 | 归纳出的规则太空泛 |
| **L4.5 [v4 新增]** | **A7 [v4 新增]** | replay test 普遍 < 60% |
| L5 / Agent | A5 | 端到端 A/B 一致率 < +20pp |

## 6.2 Phase 0 扩充(v4)

v4 在 v3 的 7 个假设上新增 **A7** 和 **A8**:

### A7 — replay test 可行性

**问题**:在 5-10 条 episode 的小样本下,leave-one-out cross-validation 能不能给出有意义的 replay accuracy 区分度?

**做法**:
1. 收集 10 条同 task 的 episode
2. 手工归纳 3 条候选规则:1 条**真规则**(基于 observable 条件)、1 条**事后合理化规则**(故意基于 declared/exception 条件,看起来合理但不可证伪)、1 条**故意错的规则**
3. 跑 leave-one-out replay
4. 期望:真规则 acc ≥ 0.7,合理化规则 acc 在 0.4-0.6,错规则 acc < 0.3

**通过标准**:三种规则的 replay accuracy 区分度 ≥ 0.3(真规则 vs 合理化规则)

**不通过的备选方案**:
- replay test 失效 → L4.5 退化为"L4 输出全部进 hypothesis 段,不进 verified 段",由人类专家做最终筛选
- 这等于把 v4 的核心假设检验循环砍掉,降级回 v3 的"endorse + 主观信任"模式

### A8 — epistemic_load 标注一致性

**问题**:同一个员工在不同时间标的 epistemic_load 一致吗?两个员工标同一组规则一致吗?

**做法**:
1. 准备 10 条候选规则
2. 让 1 名员工在 Day 5 和 Day 6 各标一次,算 test-retest reliability
3. 让另一名同岗位员工独立标一次,算 inter-rater reliability (Cohen's kappa)

**通过标准**:test-retest ≥ 0.7,IRR ≥ 0.6

**不通过的备选方案**:
- 员工标得不一致 → 说明 epistemic_load 是个主观漂移概念,不能作为硬开关
- 退化:`epistemic_load` 字段保留,但**不再决定**规则进 verified/hypothesis/reminder 哪一段;改为给所有规则都加一份"自动执行 / 仅提醒"的双版本输出,让 Agent 端配置选择

## 6.3 Phase 0 7 天节奏(v4 修订)

| 天 | 上午 | 下午 |
|---|---|---|
| Day 1 | A1 任务清单 + 部署 manifest 起草 | (同 v3) |
| Day 2 | 收集 20 条 episode | A3a immediate |
| Day 3 | A2 LLM 分类 | A6 routine 候选 |
| Day 4 | A3b deferred + **A8 第一次 epistemic_load 标注** | 手工归纳 |
| Day 5 | A4 peer review + **A8 第二次标注 (test-retest) + IRR** | A5 准备 |
| Day 6 | A5 端到端 A/B + **A7 replay test** | 数据填进 data.yaml |
| Day 7 | `verify.py` → 看 9 个假设的 PASS/FAIL | 写 v4 → v5 决策备忘 |

## 6.4 Phase 1(v4)— 闭环原型 + L4.5 stub

v4 Phase 1 在 v3 范围之上新增:

- `validator.py` — L4.5 replay test(Phase 1.5 stub)
- `models.py` — `Production` 改名为 `ProductionHypothesis`,`conditions` 升级为 typed schema
- `deployment.py` — manifest 校验 + CLI gate
- `compiler.py` — 三段 SKILL.md 输出
- Phase 0 假设 A7 / A8 验证项

**Phase 1 验收**(v4 修订):
- v3 的端到端 A/B +20pp(不变)
- A7 在真实数据上区分度 ≥ 0.3
- A8 IRR ≥ 0.6
- deployment manifest gate 在故意污染配置下能拒绝启动(单元测试)

## 6.5 epistemic_load 的实现细节

**在 L3 step 3 收集**:见 §4.2

**在 L4 归纳时**:每条 hypothesis 继承所有 source episodes 的最高 epistemic_load 标注(保守策略)

**在 L5 编译时**:
- `low` → 进 "verified rules" 或 "hypothesis rules" 段(取决于 L4.5)
- `medium` → 进对应段,但加 ⚠ 标记
- `high` → **强制**进 "reminder rules" 段,Agent 不自动执行

---

# Part F — 失败模式与边界条件

## 11. Failure Modes(v4 新增,回应 review 第 10 条)

> 一个理论必须能宣告自己失败。下面这张表把所有"系统应该停下来"的场景列出来,每一行有一个**可观测信号**和一个**明确的系统行为**。

| 失败模式 | 可观测信号 | 系统行为 |
|---|---|---|
| **Tacit floor reached** | 某 task 的 hypothesis 连续 3 轮 L3↔L4↔L4.5 迭代后 replay accuracy 仍 < 0.6 | 标记 task 为 `not_skill_harvestable`,停止对该 task 的归纳尝试,在 SKILL.md 里写一段说明 |
| **Dialogue collapse** | 同一员工连续 3 次 L3 对话 info_score < 2 | 暂停 L3 自动追问 7 天,在 status 里告知员工"系统正在打扰你,已暂停" |
| **Rule representation insufficient** | LLM 在归纳时连续 3 次输出 "I cannot express this as IF-THEN" 或同一 hypothesis 的所有 conditions 都落进 declared/exception | 把这条 hypothesis 转为自然语言注释,挂在 SKILL.md 的 "informal notes" 段,不进 verified/hypothesis/reminder 任何一段 |
| **Human-in-the-loop required** | epistemic_load: high 或 task 标签命中"法律/医疗/财务高风险" | 永远不进 "verified" 段,只进 "reminder" |
| **Subjectivity erosion** | 员工自评(每月一次)"用了系统后我对工作的掌控感下降" 或 "我感觉系统在替我决定" | 触发 deployment_mode review,可能需要降级或退出。这是一个**伦理 alarm**,不是工程指标 |
| **Manifest violation** | deployment_mode.yaml 的关键字段被改成违反 §0.4 规范前提的值 | CLI 拒绝启动,打印违反的具体字段 |
| **Drift detection** | verified rule 在生产中被 Agent 调用后连续 N 次失败 | 把 rule 从 verified 降级回 hypothesis,反向触发 L3 追问 |

**关键原则**:每一条失败模式都对应一个**降级行为**而不是"系统崩溃"。Skill Harvester 在大多数失败场景下应该能 graceful degrade,只在 manifest violation 这一类规范违反场景下才硬拒绝启动。

---

# 附录 A:v4 相对 v3 的关键变化

| 变化 | 位置 | 来源 |
|---|---|---|
| 文档结构按描述/设计/规范三段重组 | Part A/B/C | review 第 9 条 |
| §0.1 Skill 定义收窄(elicit/abstract/formalize/delegate) | §0.1 | review 第 1 条 |
| §0.2 IF-THEN 是 partial representation 的显式声明 | §0.2 | review 第 2 条 |
| §0.4 规范前提显式化 | §0.4 | review 第 6 条 |
| Part A 描述性命题独立成段, 每条带证据 | Part A | review 第 9 条 |
| Part B 设计假说独立成段, 每条对应 Phase 0 验证 | Part B | review 第 9 条 |
| Part C 规范约束独立成段 (5 项控制权) | Part C | review 第 7 条 |
| **L4.5 Hypothesis Validator 新增** | §4.4 | **review 第 3 条** |
| Production → ProductionHypothesis 重命名 | §4.3 | review 第 3 条 |
| conditions 字段类型化 (4 个子类) | §4.3 | review 第 5 条 |
| L3 step 3 epistemic_load 标注新增 | §4.2 | review 第 8 条 |
| L5 三段输出 (verified/hypothesis/reminder) | §4.5 | review 第 8 条 |
| Phase 0 新增 A7 (replay) + A8 (epistemic IRR) | §6.2 | L4.5 + epistemic_load 衍生 |
| §10 deployment manifest gate 新增 | §10 / Part C | review 第 6/7 条 |
| §11 Failure modes 表 | §11 | review 第 10 条 |
| 假二分修正 (event trace 是证据来源) | A5 | review 第 4 条 |

---

# 附录 B:仍未在 v4 内闭合的问题

见 [v4-open-questions.md](./v4-open-questions.md)。这是 v4 主动留下的"已知洞",也是 v5 的输入。

主要包括:
1. Replay test 的 ground truth 鸡生蛋问题
2. epistemic_load 的主观漂移
3. 多员工版本的规则合并裁决
4. UI 漂移检测的反向触发链路
5. deployment manifest 在多机器同步场景下的一致性

---

*v4 修订基于 v3 + 一份十条逻辑 review。完整 review 文本和逐条回应见 [CHANGELOG.md](./CHANGELOG.md) v4 章节。*
