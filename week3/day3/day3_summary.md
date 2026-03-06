# 第 3 周 Day 3 学习总结：System Prompt 设计模式 + Function Calling

> **核心目标：掌握产品级 System Prompt 设计和 Function Calling 原理。**

---

## 1. System Prompt vs User Prompt

| 维度 | System Prompt | User Prompt |
|------|--------------|-------------|
| 谁写 | 开发者 | 用户 |
| 什么时候变 | 几乎不变 | 每次对话都变 |
| 作用 | 定义角色、规则、格式 | 提供具体问题 |
| 类比 | CSS 全局样式 / React Context | 页面具体内容 / Component props |

---

## 2. System Prompt 六大设计模式

| 模式 | 作用 | 关键点 |
|------|------|--------|
| 角色设定 | 定义模型人设 | 越具体越好 |
| 输出格式控制 | 保证前端能解析 | **必须给完整 JSON schema 示例** |
| 行为边界 | 防止模型跑偏 | 明确"能做"和"不能做" |
| Few-Shot 内置 | 提升准确率 | 在 System Prompt 里放示例 |
| CoT 内置 | 提升推理能力 | 内置 "think step by step" |
| 安全兜底 | 防注入攻击 | 不泄露 Prompt、不生成有害内容 |

### 产品级模板
```
# 角色  → 定义人设
# 能力  → 能做什么 / 不能做什么
# 输出规则 → JSON schema + 格式要求
# 语气  → 友好/专业
# 安全  → 边界约束
```

### ⚠️ 关键经验
- **JSON 格式必须给完整 schema 示例**，不能只说"用 JSON 格式"
- 不给 schema → 模型字段名不稳定 → 前端 `JSON.parse()` 崩掉

---

## 3. Function Calling

### 核心工作流（4 步）

```
Step 1: 开发者定义工具（name + description + parameters）
Step 2: 用户提问
Step 3: 模型判断 → 返回函数名 + 参数（不是直接回答）
Step 4: 开发者代码执行函数 → 结果喂回模型 → 生成最终回答
```

### 核心理解
- **模型不执行函数！** 只决定"调什么、传什么参数"
- 执行是开发者的代码做的
- 前端类比：模型 = 前端（发请求），你的代码 = 后端（处理请求）

### 面试考点
- **模型怎么知道调哪个函数？** → 通过你定义的工具 description（JSON Schema）
- **工具描述的质量决定准确率** → 像写好的 API 文档
- **工具数量建议 ≤ 20 个** → 太多准确率下降

---

## 4. 避坑指南

1. **System Prompt 要迭代优化**，不是一次写好
2. **JSON schema 必须明确**：字段名、类型、示例值全部写死
3. **Function Calling 要做参数校验**：模型可能传错类型
4. **Code Interpreter ≠ 模型执行代码**：是沙箱服务器执行的

---

## 5. 下一步学习

**明天内容**：Prompt 注入攻击与防御

**预习问题**：
1. 用户可以怎样"欺骗"模型忽略 System Prompt？
2. 如何检测和防御 Prompt 注入？
