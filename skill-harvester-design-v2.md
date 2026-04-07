# Skill Harvester — 项目设计文档 v2

> **v2 修订说明**：本版本基于对 v1 的多轮 review，修正了三个核心问题：
> 1. **goal 识别**这一隐藏循环依赖被显式化 —— 引入"日常任务清单"作为系统元数据基座
> 2. **可行性证伪**前置 —— 新增 Phase 0，用一周纸笔 + 真 LLM 验证三个生死假设
> 3. **意图与执行解耦** —— L4 只产业务规则，L5 把业务动作映射到具体工具调用，避免 UI 漂移导致 skill 失效
>
> v1 的核心叙事（隐性知识、ACT-R compilation 反向跑、surprisal 触发）保持不变。

---

## 0. 系统的核心信念（前置）

> **Skill 不是行为的录音，而是判断的化石。**

Skill Harvester 的工作不是看员工的手，而是**蹲守员工那些不得不停下来想一想的瞬间**，用对话把那一下的思考从他脑子里取出来，编译成可以被任何 Agent 复用的 IF-THEN 规则。

这就是把 ACT-R 的 compilation 倒过来跑 —— 人脑把陈述性知识压成程序性知识，我们把程序性知识再拉回陈述性知识，并保留它的可执行形式。这种"既隐性又可读"的中间态，恰好就是 SKILL.md 的本质。

---

## 1. 系统成立的前置假设（Critical Assumptions）

整个系统建立在以下五个假设之上。任何一个被证伪，整个项目必须改方向，而不是继续推进。Phase 0 的全部工作就是用一周时间逐条验证这些假设。

| # | 假设 | 证伪信号 | 备选方案 |
|---|---|---|---|
| A1 | 员工能写出一份**具体到动宾结构**的"日常任务清单"，覆盖一天 80% 的工作 | 员工写不出来或写得空泛 | 工作太碎片化，需要重新选目标用户 |
| A2 | 给定任务清单 + 当前 episode 的文本特征，**LLM 能做高置信度的 goal 分类** | 高置信度子集占比 < 50% 或准确率 < 90% | 加入截图视觉信号；再不行退回"每条都问 goal" |
| A3 | 员工在事后追问下，能对自己的"困难瞬间"给出**有信息量的反事实回答** | 回答模糊、事后合理化、低于主观 3 分（1-5 标度） | 缩短追问延迟到分钟级；再不行整个 L3 退化为辅助标注工具 |
| A4 | 5-10 条同类 episode 配上员工外化条件，**LLM 能归纳出一条让另一名同岗位员工认可的 IF-THEN 规则** | 第二位员工无法认可或无法指出具体不准确点 | 等待更大样本量；或退回 active probing 模式 |
| A5 | 编出的 SKILL.md 能让一个新的 Agent 在同类案例上的**判断一致率显著高于无 skill 对照组** | A/B 一致率差距 < 20pp | 中间表示选错；换格式重试 |

**Phase 0 的全部产物 = 这五个假设的证伪报告。**

---

## 2. 问题陈述

### 2.1 表层问题
要让 AI Agent 学会一个领域专家的工作方式，最直接的想法是"录下专家在电脑上的所有操作然后训练模型"。这条路有三个致命问题：

1. **绝大多数行为没有信息量** —— 每天的鼠标点击 99% 是套路动作。
2. **工作流中夹杂大量琐碎动作** —— 切窗口、复制粘贴、滚动浏览，是噪声不是信号。
3. **录屏存储成本爆炸** —— 一天 8 小时高分辨率录屏可达数十 GB。

### 2.2 深层问题
即使解决了存储问题，纯行为录制也学不到专家的真正技能：

- **专家最值钱的知识恰恰是他自己说不清的那部分**（Polanyi: *We know more than we can tell*）
- 这部分知识在 ACT-R 框架里叫**程序性产生式**（procedural productions），已从陈述性记忆下沉到自动化执行
- 行为流只能记录产生式的"右手边"（动作），完全丢失了"左手边"（条件），所以无法泛化

### 2.3 真正要解决的问题
**如何用最小的采集开销，最大化地还原员工脑子里的 IF-THEN 决策规则集，并把它编译成可被 Agent 直接调用的 SKILL.md？**

---

## 3. 核心设计原则

1. **信息 = 惊讶度** (Shannon / Predictive Coding) — 存储量正比于 surprisal，不正比于时间
2. **困难是黄金信号** (Klein RPD / Dreyfus) — 隐性知识只在异常时才被迫浮回工作记忆
3. **条件不能被观察，只能被询问** (Polanyi / CTA) — 必须有一个反事实对话层主动外化隐性条件
4. **奥卡姆剃刀的算法形式 = MDL** — 优选短规则、高覆盖率规则
5. **机器编译必须保留可读性** — 最终产物必须是 Markdown，可被人类专家审计修订
6. **【新增】Goal 不靠猜，靠先验 + 询问** — 系统不试图从屏幕推断"员工在做什么"，而是用员工预先写的任务清单做分类，低置信度时回退到询问
7. **【新增】意图与执行解耦** — 业务规则和 UI 操作必须分两层存储，让 UI 改版时只需重写执行映射，不需重新归纳业务规则

---

## 4. 系统架构

### 4.1 六层架构（v2 在 v1 上加了 L0）

```
┌─────────────────────────────────────────────────┐
│  L5  Skill Compiler          → SKILL.md         │  产物层（KB级）
├─────────────────────────────────────────────────┤
│  L4  Production Inducer      → IF-THEN 规则集    │  归纳层（KB级）
├─────────────────────────────────────────────────┤
│  L3  Dialogue Engine         → 反事实问答记录     │  外化层（MB级）
│       step 1: goal 自动分类                      │
│       step 2: 反事实追问                         │
├─────────────────────────────────────────────────┤
│  L2  Episode Builder         → 困难瞬间快照       │  采样层（MB级）
├─────────────────────────────────────────────────┤
│  L1  Sparse Sensor           → 语义边界事件流     │  感知层（KB/天）
├─────────────────────────────────────────────────┤
│  L0  Task Catalog            → 日常任务清单       │  元数据层（< 1KB）
└─────────────────────────────────────────────────┘
```

**关键变化**：L0 是 v2 新增的元数据基座。L1–L5 全都依赖 L0。

---

### 4.2 L0 — Task Catalog（任务清单层）【新增】

**职责**：存储员工自己写的、对自己日常工作的"陈述性自述"，作为整个系统的元数据基座。

**为什么需要这一层**：v1 的循环依赖在于 L1/L2 都假设"上游已经识别出 goal"，但没有任何组件真正负责 goal 识别。v2 把这个问题搬到 L0，并采用最朴素的方案 —— 让员工自己写。

**写法约束**：
- **强制动宾结构**：必须是"动词 + 具体宾语"，例如"处理退款工单"，而不是"维护客户关系"
- **5-15 项**，覆盖一天 80% 的时间
- **必须包含"以上都不是 / 临时任务"兜底项**
- **写的时候对着真实痕迹**（最近一周的日历、邮件、工单），而不是对着岗位说明书凭空想

**Schema**（YAML）：
```yaml
employee_id: emp_001
employee_role: customer_service_senior
tasks:
  - id: refund_handling
    label: 处理退款工单
    description: 在 ERP 中审批客户提交的退款申请
    typical_apps: [Outlook, ERP]
    typical_keywords: [refund, 退款, Stornorichtlinie]

  - id: shipping_inquiry
    label: 回复物流查询邮件
    description: 客户问"我的包裹到哪了"，查物流后回复
    typical_apps: [Outlook, DHL Portal]
    typical_keywords: [tracking, 物流, 包裹]

  # ... 5-15 项

  - id: other
    label: 临时任务 / 以上都不是
    description: 兜底项，触发开放式 goal 询问
```

**动态生长**：L0 不是一次性产物。L4 在归纳过程中如果发现某个 task 内部存在明显分裂（同一 task 走了系统性不同的分支），会**反向建议**员工拆分；如果发现大量 episode 落进 `other`，会**建议**员工新增 task。员工每周花 5 分钟 review 一次 L0 的修订建议。

---

### 4.3 L1 — Sparse Sensor（稀疏感知层）

**职责**：以最低开销持续监听用户工作环境，只产出语义边界事件。**不再尝试推断 goal**。

**默认状态：沉默。** 仅在以下五类事件触发时输出一条记录：

| 事件类型 | 示例 | 含义 |
|---|---|---|
| 任务边界 | 打开新工单、收到新邮件、切换项目 | 新目标可能开始 |
| 决策边界 | 表单提交、文件保存、确认对话框 | 决策落地 |
| **异常边界** ⭐ | 错误对话框、撤销、长停顿（>5s）、反复切窗口 | **困难发生（黄金信号）** |
| 查询边界 | 复制操作、打开搜索框、切到浏览器 | 信息获取 |
| 显式标记 | 全局快捷键 Ctrl+Alt+M | 人在回路 |

**【v2 修正】novelty 判定**：v1 提议用本地 n-gram 模型，v2 改为：
- **Phase 1**：根本不算 novelty。只看硬信号（停顿/撤销/外部查询/显式标记），宁可多收不可漏收
- **Phase 2**：用 AX Tree 拓扑变化（DOM/AX 树的大块修改、焦点无序切换）做 novelty 信号，比 n-gram 稳健

**预期输出量**：~几百 KB / 天 / 员工。无截屏。

---

### 4.4 L2 — Episode Builder（情节构建层）

**职责**：把 L1 的稀疏事件聚合成有头有尾的情节，每条情节对应一次有意义的工作单元。

**切分规则**：
- **起点**：上一个"任务边界"或"显式标记"事件
- **终点**：下一个"决策边界"事件，或超过 N 分钟无新事件
- **提交触发**：情节中至少包含一个高 surprisal 信号，或员工显式标记
- **不满足条件 → 直接丢弃**

**仅在情节被提交时**才触发高分辨率上下文捕获：截图 + accessibility tree + 剪贴板 + 最近 30 秒环形缓冲。这是整个系统**唯一会产生大文件的地方**。

**Episode schema**（v2 修正：**移除了 v1 的 `goal_hint`** —— 这个字段是循环依赖的源头）：
```json
{
  "episode_id": "ep_20260407_001",
  "ts": "2026-04-07T10:23:14",
  "trigger": "long_pause + undo_burst",
  "duration_s": 142,
  "events": [...],
  "snapshot_path": "ep_20260407_001.png",
  "context": {
    "active_app": "Outlook",
    "window_title": "Re: Order #4471 refund",
    "url": null,
    "clipboard_excerpt": "Order #4471, 55 EUR"
  },
  "tacit_signals": {
    "pauses": [{"at": 8.2, "before": "Approve"}],
    "undos": 2,
    "external_lookups": ["搜索 'Stornorichtlinie >50€'"]
  },
  "goal": null,             // 由 L3 step 1 填写
  "goal_confidence": null,  // 同上
  "dialogue": null          // 由 L3 step 2 填写
}
```

---

### 4.5 L3 — Dialogue Engine（外化对话层）【v2 重大修订】

**职责**：分两步完成 episode 的语义补全 —— 先识别 goal，再外化隐性条件。

#### Step 1: Goal 自动分类（v2 新增）

**输入**：episode 的文本特征 (`active_app`, `window_title`, `url`, `clipboard_excerpt`, 事件序列摘要) + L0 任务清单

**模型**：轻量 LLM（本地 7B 或 cloud 小模型）

**Prompt 模板**：
```
员工的日常任务清单如下：
{L0 yaml}

刚才发生了一个工作片段，特征如下：
{episode 文本特征}

请判断这个片段属于清单里的哪一项任务。
输出 JSON：{"task_id": "...", "confidence": 0.0-1.0, "reason": "..."}
```

**输出**：`(task_id, confidence)`

**置信度阈值**（`THETA`）：
- Phase 1：**不设阈值，全部都问员工确认**，把 LLM 输出 + 员工答案存下来
- Phase 1 末尾：根据数据校准阈值（找到使"高置信度子集准确率 ≥ 95%"的最大覆盖率阈值）
- Phase 2 上线：只问 `confidence < THETA` 的部分

#### Step 2: 反事实追问

**触发时机**（绝不打断工作）：
- 默认：每日尾声 5 分钟批处理
- **可选缩短延迟**：在 episode 触发后 30 分钟内的下一个"自然停顿点"（鼠标静止 30s + 无键盘输入）弹出，缓解事后合理化
- 永远不打断正在进行的工作 —— hard rule

**追问形式**（v2 修正：**优先选择题，而不是开放题**）：

| 信号 | 追问类型 | 示例 |
|---|---|---|
| 长停顿在某动作前 | **选择题决策点** | "你最终点了【Approve】之前停了 8 秒。最影响这个判断的是：A. 订单金额（55€）；B. 客户历史；C. 退货原因；D. 其他 ___" |
| 撤销 | 反事实选择题 | "你先选了 Escalate 又改成 Approve，是因为看到了：A. 金额低于阈值；B. 客户是老用户；C. 其他 ___" |
| 外部查询 | 知识缺口询问 | "你查了退货政策。是这单有什么特殊？以后什么情况下你也会去查？" |
| 多 episode 走不同分支 | **对比追问** ⭐ | "上周一单 60€ 你直接批了，今天 55€ 你升级了，差别在哪？" |

**回答存进 episode 的 `dialogue` 字段，形成 (动作, 隐性条件) 训练对。**

---

### 4.6 L4 — Production Inducer（产生式归纳层）

**职责**：把 L3 输出的"动作 + 外化条件"对归纳成参数化 IF-THEN 规则集。

**运行方式**：离线批处理。

**流程**：
1. **聚类**：按 `task_id`（来自 L3 step 1）把 episode 分组 —— v2 不再用 embedding 聚类，因为 L0 的 task_id 已经是受控词汇表
2. **分裂检测**：在同 task 内找出"走了不同动作分支"的 episode 对
3. **条件归纳**：把分裂双方的上下文 + 员工对话回答喂给 LLM，输出候选规则
4. **MDL 评估**：优选"短规则 + 高覆盖率"的规则集
5. **冲突解决**：按 Anderson 的 utility 分数排序（成功使用 / 总匹配）

**【v2 关键修正】中间表示采用 "意图 / 执行" 双层**：

```yaml
production:
  id: refund_auto_approve
  task_id: refund_handling

  # === 意图层（业务规则，与 UI 无关）===
  intent:
    goal: process_refund
    conditions:
      - order_amount < 50 EUR
      - customer_tenure_months > 6
      - has_no_prior_disputes
    business_action: approve_refund
    rationale: "small_amount_trusted_customer"

  # === 执行层（具体工具/UI 调用，可被 self-heal 重写）===
  execution:
    tool: erp_mcp.click_button
    args:
      button_label: Approve
      window: "Refund Detail View"
    fallback_tool: browser_use
    fallback_hint: "Find a button labeled Approve or 批准"

  # === 元数据 ===
  utility: 0.94   # 47/50
  source_episodes: [ep_20260301_003, ep_20260315_007, ...]
  confidence: high
```

**这个修正直接回答 v1 的 Open Question 4（Skill 漂移）**：UI 改版时，只需要 self-heal `execution` 段，意图层的归纳成果完全保留。

---

### 4.7 L5 — Skill Compiler（Skill 编译层）

**职责**：把 L4 的产生式集合编译成 SKILL.md，放进现有 skills 目录。

**输出 SKILL.md 的结构**（v2 明确）：
```markdown
---
name: refund_handling
description: 处理客户退款工单的决策规则
trigger_keywords: [refund, 退款]
source: skill-harvester
employee_id: emp_001
generated_at: 2026-04-07
---

# 退款处理规则

## 业务规则（意图层）

### Rule 1: 小额可信客户自动批准
**当**：
- 订单金额 < 50 EUR
- 客户注册超过 6 个月
- 无历史争议
**则**：approve_refund
**理由**：小额可信客户，按经验直接批准
**置信度**：0.94 (基于 47/50 条 episode)

### Rule 2: ...

## 执行映射（工具层）

| 业务动作 | 首选工具 | Fallback |
|---|---|---|
| approve_refund | erp_mcp.click_button(Approve) | browser_use |
| escalate_refund | erp_mcp.click_button(Escalate) | browser_use |

## 来源审计
- Rule 1 基于 episodes: [ep_20260301_003, ...] [查看截图]
- Rule 2 基于 episodes: [...]
```

**草稿放进 `skills/pending/` 目录，等待人类 review** —— hard rule。

---

## 5. 横切关注

### 5.1 隐私与合规
- L1 支持按应用 / 时间段 / 窗口标题白黑名单
- 所有数据**本地存储**，绝不出本机
- L2 截图前跑 OCR + PII 过滤器
- **【v2 新增】双部署模式**：
  - **个人模式**：员工自装、数据自管，无监控嫌疑，**绕开 BetrVG §87**
  - **团队模式**：需要 Betriebsrat 协议
  - Phase 1/2 默认走个人模式
- 托盘常驻"暂停录制"开关：30 分钟 / 一天 / 永久

### 5.2 可审计性
每条进入正式 `skills/` 目录的规则必须能反向追溯到原始 episode + 截图 + 员工对话。

### 5.3 冷启动友好
- 【v2 新增】用现有 SOP 文档（如果有）反向编译出"含糊基线" SKILL.md，Harvester 在基线上发现特例
- 用户感知层：每天反馈"今天捕获 X 个困难瞬间，下周可生成首批规则草稿"

---

## 6. MVP 路线图（v2 修订）

### Phase 0：可行性证伪（1 周，零代码或最少代码）

**目标**：验证 §1 的五个假设。任何一个不成立，改方向。

**做法**：
1. 选 1 名目标员工（不是窄领域，是窄"用户"）
2. 让员工写 L0 任务清单（30 分钟，强制动宾结构）
3. 让员工正常工作半天，手动按热键标记 20 条"困难瞬间"
4. 用最朴素的 prompt 跑真 LLM 做 goal 分类，对照员工 ground truth 算指标
5. 你/团队手工扮演 L3 step 2（反事实追问）+ L4 + L5
6. 把产物 SKILL.md 拿给另一名同岗位员工 + 一个新 Agent 测试

**并行任务**：起草 Betriebsrat 协议草案大纲。

**通过标准**：§1 表格中的五个证伪信号都没有触发。

### Phase 1：闭环原型（2-3 周，仅 Phase 0 全部通过才启动）

**范围**：
- L0：YAML 文件 + 加载器
- L1：**最笨版本** —— 全局热键 Ctrl+Alt+M，按下时截屏 + 抓窗口标题/app + 最近 30 秒事件
- L2：每按一次热键就是一条 episode，无自动切分
- L3：自动 goal 分类（调真 LLM）+ CLI 反事实追问
- L4：CLI 触发的批处理归纳脚本
- L5：编译 SKILL.md 草稿到 `skills/pending/`

**不做**：跨平台、AX Tree、自动 surprisal 检测、self-heal、隐私合规 UI、生产部署。

**验收**：端到端 A/B —— 30 条手动 episode 编出的 SKILL.md，让 Agent 在新案例上的一致率比无 skill 高 ≥ 20pp。

### Phase 2：半自动采集（3-4 周）
- L1 升级为系统级 hook（先选一个平台，例如 macOS）
- L1 引入 AX Tree 拓扑变化作为 surprisal 信号
- L2 自动切分 episode
- 冷启动用 SOP 反向编译

### Phase 3：全栈采集 + 治理（6-8 周）
- 跨平台
- 隐私合规层（PII 过滤、白黑名单 UI、暂停录制）
- 审计 UI（episode 浏览器、规则溯源）
- self-heal 执行层
- 双部署模式落地

---

## 7. 与现有 Cowork 体系的关系

```
                  ┌──────────────┐
                  │ skill-creator│  ← 人类直接写 Skill
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │  skills/     │  ← Agent 调用入口
                  └──────▲───────┘
                         │
                  ┌──────┴────────┐
                  │ skill-harvester│ ← 从员工行为编译 Skill
                  └───────────────┘
```

Skill Harvester 不替换 skill-creator，而是**扩展知识来源**。两者最终汇入同一个目录，对 Agent 完全透明。

---

## 8. v2 待决问题

1. **L3 step 1 的最优 prompt 形式**：是否需要把截图也喂给多模态 LLM？文本信号够不够？—— 在 Phase 0 测出来
2. **置信度阈值校准**：高置信度子集的准确率分布形状 —— 在 Phase 1 末尾测出来
3. **L4 在归纳时如何"自动建议拆分 L0 task"**：算法形式还需要设计
4. **个人模式下的"自我学习"激励**：员工为什么要持续用？需要从他自己的产出里看到价值
5. **跨员工知识合并**：v1 的 Open Question 3 仍未解决，留给 Phase 3

---

## 附录 A：v2 相对 v1 的关键变化清单

| 变化 | 位置 | 来源 |
|---|---|---|
| 新增 §0 核心信念前置 | §0 | review 建议结构调整 |
| 新增 §1 五个前置假设 + 证伪信号 | §1 | review 假设风险驱动 |
| 新增 L0 Task Catalog 层 | §4.2 | 用户提出 + 修正循环依赖 |
| L3 拆成 step 1 (自动分类) + step 2 (反事实) | §4.5 | 用户提出 |
| L3 step 2 优先选择题而非开放题 | §4.5 | 缓解事后合理化 |
| L4 中间表示拆为意图层 + 执行层 | §4.6 | review 建议（意图-执行分离）|
| L1 移除 n-gram，Phase 1 不算 novelty | §4.3 | review 建议 |
| Episode schema 移除 goal_hint | §4.4 | 解决循环依赖 |
| 新增 Phase 0 可行性证伪阶段 | §6 | review 假设风险驱动 |
| 新增双部署模式（个人/团队）| §5.1 | review 合规风险 |
| 冷启动用 SOP 反向编译 | §5.3 | review 建议 |
| Phase 1 验收改为端到端 A/B | §6 | review 建议客观验收 |

---

*本文档 v2 基于 v1 与多轮 review 对话编译而成。设计选择可追溯到 Polanyi 的隐性知识理论、Anderson 的 ACT-R 框架、Klein 的 RPD 模型、Zacks 的事件分割理论，以及 Shannon 的信息论。*
