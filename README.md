# Skill Harvester 

> Skill 不是行为的录音，而是判断的化石。
> 一个把员工脑子里沉默的产生式（productions）"逼"出来、写下来、编译成可执行 SKILL.md 的认知任务分析自动化系统。

## 理论基座与设计哲学：什么是 Skill？

从逻辑学和认知科学的视角来看，"Skill"（技能）指向同一个核心现象：把显式的知识，压缩成可直接调用的自动化程序。

1. **逻辑学视角（“Knowing How”到“Knowing That”的逆向翻译）**
   Gilbert Ryle 区分了命题性知识（Knowing That）和程序性知识（Knowing How）。Skill 本质上是后者的载体——它是一种“直接做对”的非单调倾向。系统的工作，就是把隐性的 Knowing How 重新抽成一条条含有前置条件（IF）的 Knowing That，从而避免无穷溯源。
2. **认知科学视角（ACT-R 与隐性知识逆编译）**
   Fitts 和 Posner 认为技能是从“认知”逐步走向“自动化”的。在 ACT-R 理论中，这就是“知识编译（Knowledge Compilation）”过程——陈述性知识打包变成了程序性产生式，因此专家往往“说不清为什么（Polanyi：*Tacit Knowledge*）”。
   Dreyfus 的专长模型指出，专家依靠模式识别取代规则；此时，纯粹观察“点击流（RPA）”是学不会专家的，因为没有获取其**意图与上下文**。

**Skill Harvester 的哲学：** 通过捕捉“困难瞬间（预测误差峰值）”，强行打断专家的流状态（Flow），把程序性产生式再度拉回工作记忆进行显性表达（反事实追问）。这不是录屏工具，而是**自动化认知任务分析（Cognitive Task Analysis）系统**。

## 核心设计与奥卡姆剃刀

工作流中夹杂了大量琐碎动作，真正的有效决策隐藏在海量的无意义点击中。系统如何用最小的路径达成目标？
大脑面临每秒 10^7 bit 流入时选择了“预测编码（Predictive Coding）”，系统也是基于同样的第一性原理设计：

1. **信息量 = 惊讶度（Surprisal）**：系统不记录日常平淡无奇的动作组合，因为它们的信息量接近 0。系统只在“困难导致犹豫”的瞬间睁眼。
2. **盯住“黄金瞬间”**：我们只收集长停顿、取消重做、外部系统查询等发生异常波动的节点。
3. **隐性知识只有遇到困难才被激活**：我们引入反事实追问（Cognitive Task Analysis）的方式，在自然休息节点提问员工，把“当时怎么想的”剥离出来。

## 系统五层架构

本系统由下至上包含了五层信息压缩机制，逐层提纯员工的操作：

1. **L0 Task Catalog (任务清单)**: 提供先验意图，员工的显性日常工作声明。
2. **L1 Sparse Sensor (稀疏感知层)**: 以极低开销监听事件流（仅关注焦点切换、剪贴板、报错等宏观边界）。
3. **L2 Episode Builder (情节构建层)**: 仅在预测误差高峰处触发保存“情节”快照与环形缓冲。
4. **L3 Dialogue Engine (外化对话引擎)**: 在恰当时机发起反事实提问，剥离出真实的决策条件。
5. **L4 Production Inducer (产生式归纳层)**: 寻找不同 episode 的分支节点，提取 IF-THEN 逻辑并解耦业务意图与 UI 执行。
6. **L5 Skill Compiler (系统编译层)**: 将推理结果落地为 Agent 能够直接执行的 `.md` Skill 脚本文件。

详见设计文档：
- [skill-harvester-design.md](./skill-harvester-design.md) — v1 原始设计
- [skill-harvester-design-v2.md](./skill-harvester-design-v2.md) — **v2 修订版（推荐先读这个）**

## 运行：Phase 1 MVP

本仓库目前处于 Phase 1 闭环原型阶段。目标是**让 L3→L4→L5 这条链路能跑通一次**，完成“手动 episode 提交 -> 产生式编译”的验证。

### 快速开始

```bash
# 1. 安装
pip install -e .

# 2. 准备任务清单
cp examples/task_list.example.yaml ~/.skill-harvester/task_list.yaml
# 编辑 task_list.yaml，写入员工的真实任务

# 3. 启动 Phase 0 的"按键采集"模式
skill-harvester capture
# 在工作时按 Ctrl+Alt+M 标记一个困难瞬间

# 4. 当晚做反事实追问
skill-harvester review

# 5. 攒够 episode 后跑归纳
skill-harvester induce

# 6. 编译成 SKILL.md
skill-harvester compile

# 输出：./skills/pending/<task_id>.md
```

### 环境配置

默认使用 mock backend 进行本地实验。如需接入真实模型：
```bash
export SKILL_HARVESTER_LLM=anthropic   # 或 openai / mock
export ANTHROPIC_API_KEY=...
```

### 项目结构

```
skill_harvester/
├── models.py       # 数据结构：TaskCatalog, Episode, Production
├── storage.py      # Episode 序列化与存储
├── llm.py          # LLM 后端抽象
├── capture.py      # L1/L2: 热键采集与片段构建
├── classifier.py   # L3 step 1: Goal 语义分类
├── dialogue.py     # L3 step 2: 交互式反事实追问
├── inducer.py      # L4: 逻辑提纯与产生式归纳
├── compiler.py     # L5: Markdown Skill 编译
└── cli.py          # 命令行入口
```

*本项目基于 Programming by Demonstration 的现代范式构建，将个人沉默的行动固化为组织的通用生产力枢纽。*
