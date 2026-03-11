# 第 5 周 Day 5 学习总结：Multi-Agent 多智能体架构

> **核心目标：理解 Multi-Agent 的三大框架对比、角色分工设计、通信协议实现，能在面试中设计完整的 Multi-Agent 系统。**

---

## 1. 为什么需要 Multi-Agent？

单个 Agent 的局限：

```
单 Agent 的问题：
- 上下文窗口有限，复杂任务容易"忘事"
- 一个模型同时扮演多个角色，容易混乱
- 无法并行处理多个子任务
- 单点故障，一个环节出错全盘崩溃

Multi-Agent 的解法：
- 每个 Agent 专注一个角色（程序员/审查员/测试员）
- 角色之间通过消息传递协作
- 可以并行执行独立子任务
- 一个 Agent 失败不影响其他 Agent
```

**真实场景**：
- 代码生成：Coder 写代码 → Reviewer 审查 → Tester 测试
- 内容创作：Writer 写初稿 → Editor 润色 → Fact-checker 核实
- 客服系统：意图识别 Agent → 业务处理 Agent → 回复生成 Agent

---

## 2. 三大框架对比（面试必背）

| 维度 | CrewAI | AutoGen | LangGraph |
|------|--------|---------|-----------|
| 核心抽象 | 角色（Role） | 对话（Conversation） | 图（Graph） |
| 控制粒度 | 低（高层封装） | 中 | 高（精细控制） |
| 上手难度 | 简单 | 中等 | 较难 |
| 适用场景 | 快速原型、角色驱动 | 多轮对话协作 | 复杂流程、精细控制 |
| 核心优势 | 声明式定义角色和任务 | 灵活的对话管理 | 状态机 + 条件分支 |

### CrewAI：角色驱动

```python
from crewai import Agent, Task, Crew

# 声明式定义角色
coder = Agent(
    role="Python 程序员",
    goal="编写高质量的 Python 代码",
    backstory="8 年经验的资深工程师"
)

reviewer = Agent(
    role="代码审查员",
    goal="找出代码中的 Bug 和安全隐患",
    backstory="前 Google 工程师，极其严苛"
)

# 定义任务和流程
task = Task(description="实现一个去重函数，不能用 set()", agent=coder)
crew = Crew(agents=[coder, reviewer], tasks=[task])
crew.kickoff()
```

**适合**：快速搭建原型，角色职责清晰的场景

### LangGraph：图结构控制流

```python
from langgraph.graph import StateGraph

# 用图来定义 Agent 的执行流程
graph = StateGraph(AgentState)
graph.add_node("coder", coder_node)
graph.add_node("reviewer", reviewer_node)

# 条件边：审查通过 → 结束，不通过 → 回到 coder
graph.add_conditional_edges(
    "reviewer",
    lambda state: "end" if state["approved"] else "coder"
)
```

**适合**：需要精细控制流程、有复杂条件分支的场景

### 核心区别（面试一句话）

> "CrewAI 是角色驱动的高层抽象，适合快速原型；LangGraph 是图结构的精细控制，适合复杂流程。"

---

## 3. Orchestrator 的作用

**定义**：Multi-Agent 系统的"总指挥"，负责全局调度。

**四大职责**：

```
1. 任务拆解：把复杂任务分解为子任务
   "开发一个登录功能" → [设计API, 写代码, 写测试, 写文档]

2. 角色分工：把子任务分配给合适的 Agent
   设计API → ArchitectAgent
   写代码  → CoderAgent
   写测试  → TesterAgent

3. 通信机制：管理 Agent 之间的消息传递
   CoderAgent 完成 → 把代码传给 ReviewerAgent

4. 冲突消解与全局调度：
   两个 Agent 意见冲突时，Orchestrator 做最终决策
   某个 Agent 超时，Orchestrator 决定重试还是跳过
```

---

## 4. 通信协议：消息传递（Message Passing）

**最经典的通信方式**，Agent 之间通过消息队列传递结果。

```python
def run_multi_agent_company(requirement, max_rounds=3):
    coder = CoderAgent()
    reviewer = ReviewerAgent()

    feedback = None

    for round_idx in range(1, max_rounds + 1):
        # 1. Coder 根据需求（或上轮反馈）生成代码
        code = coder.generate_code(requirement, feedback)

        # 2. Reviewer 审查代码，返回结构化结果
        review = reviewer.review_code(code)

        if review["approved"]:
            return code  # 通过，结束循环

        # 3. 把 Reviewer 的意见作为消息传回给 Coder
        feedback = review["comments"]  # ← 这就是"消息传递"

    return code  # 达到最大轮次，强制结束
```

**消息传递的关键设计**：
- 消息格式要结构化（JSON），方便解析
- 每个 Agent 维护自己的 `history`，保持上下文
- Orchestrator 负责路由消息到正确的 Agent

**其他通信方式**：

| 方式 | 说明 | 适用场景 |
|------|------|---------|
| 消息传递 | Agent 直接互发消息 | 简单线性流程 |
| 共享状态 | 所有 Agent 读写同一个状态对象 | LangGraph |
| 黑板系统 | 中央黑板存储，Agent 订阅感兴趣的内容 | 复杂多 Agent |

---

## 5. 实战代码：Coder + Reviewer 双 Agent

文件路径：`week5/day5/multi_agent_demo.py`

**架构图**：

```
用户需求
   ↓
CoderAgent（System Prompt：资深程序员）
   ↓ 生成代码
ReviewerAgent（System Prompt：严苛审查员）
   ↓ 返回 JSON {"approved": bool, "comments": "..."}
   ├── approved=True  → 输出最终代码
   └── approved=False → feedback 传回 CoderAgent → 重新生成
                        （最多 3 轮）
```

**核心设计亮点**：

```python
class ReviewerAgent:
    def review_code(self, code):
        # 低温度（0.1）保证审查结果严谨、稳定
        review_result = call_llm(self.history, temperature=0.1)

        # 结构化输出：强制 JSON 格式，方便程序解析
        # {"approved": false, "comments": "缺少边界检查..."}
        return json.loads(review_result)
```

**两个关键技巧**：
1. **不同角色用不同 temperature**：Coder 用 0.7（创造性），Reviewer 用 0.1（严谨性）
2. **强制结构化输出**：System Prompt 要求返回 JSON，方便 Orchestrator 解析和路由

---

## 6. 面试考点汇总

### 问法 1："CrewAI 和 LangGraph 怎么选？"

**标准答案**：
> "看控制粒度需求。CrewAI 是角色驱动的高层抽象，声明式定义角色和任务，适合快速原型和角色职责清晰的场景。LangGraph 是图结构，能精细控制每个节点的执行逻辑和条件分支，适合复杂流程。生产环境中复杂业务逻辑用 LangGraph，快速验证想法用 CrewAI。"

### 问法 2："Multi-Agent 系统中 Agent 之间怎么通信？"

**标准答案**：
> "主要三种方式：消息传递（Agent 直接互发结构化消息，最常见）、共享状态（所有 Agent 读写同一状态对象，LangGraph 用这种）、黑板系统（中央存储，Agent 订阅感兴趣的内容，适合复杂多 Agent）。消息格式建议用 JSON，方便解析和路由。"

### 问法 3："设计一个代码生成的 Multi-Agent 系统"

**标准答案**：
> "用 Coder + Reviewer 双 Agent 结构。Coder 的 System Prompt 定义为资深程序员，temperature 设 0.7；Reviewer 的 System Prompt 定义为严苛审查员，temperature 设 0.1，强制返回 JSON 格式结果。Orchestrator 负责消息路由：审查通过则输出，不通过则把 comments 传回 Coder 重新生成，设置最大轮次防止死循环。"

**加分项**：
- 能说出不同角色用不同 temperature 的原因
- 能说出强制结构化输出的必要性
- 能说出最大轮次限制（防止死循环）

---

## 7. 真实踩坑经历

**坑 1：Reviewer 返回格式不稳定**
> 一开始 Reviewer 的 System Prompt 没有强制 JSON，有时返回"代码有问题，建议修改..."，有时返回 JSON。Orchestrator 解析失败导致整个流程崩溃。后来在 System Prompt 里加了"你必须、绝对只能返回合法 JSON"，稳定性大幅提升。

**坑 2：没有最大轮次限制**
> Reviewer 设置得太严苛，Coder 怎么改都过不了，陷入无限循环。加了 `max_rounds=3` 后，超过轮次强制结束，避免资源耗尽。（这也是为什么 Day6 要学循环检测！）

**坑 3：所有 Agent 共用同一个 history**
> 一开始把 Coder 和 Reviewer 的对话历史混在一起，导致 Reviewer 看到了 Coder 的内部思考过程，审查结果变得奇怪。改成每个 Agent 维护独立的 `self.history` 后解决。

---

## 8. 知识点关联图

```
Week5 Day5 Multi-Agent
        ↓ 依赖
Day3 工具调用（Agent 的能力来源）
Day4 记忆系统（Agent 的 history 管理）
        ↓ 延伸
Day6 可靠性工程（Multi-Agent 的幻觉检测、循环检测）
Day7 综合实战（把所有能力组合成完整 Agent）
```

---

**导师寄语**：
> Multi-Agent 是 Agent 开发的"高级形态"，面试官问这个是想看你有没有做过真实的多角色协作系统。记住核心：每个 Agent 专注一个角色，通过结构化消息传递协作，Orchestrator 负责全局调度。Coder+Reviewer 这个经典结构一定要能手写出来。

**下一步**：Week5 Day6 Agent 可靠性工程 ⭐⭐⭐⭐⭐
