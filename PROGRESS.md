# AGI 学习进度总结（接力文档）

> 用途：开启新对话时，将此文件内容粘贴进去，让 AI 快速理解你的学习背景和进度。

---

## 学员背景

- 前端开发（React/Vue/TS 熟练），Python 入门级，无 AI/ML 经验
- 目标：通过一线大厂 AGI 开发岗面试
- 教学原则：**先写代码，遇到问题再讲原理；遇到 bug 先让学员自己定位，引导而不给答案**

---

## 已完成模块

### ✅ 1. RAG 系统（核心，week6/day5/rag.py）

| 功能 | 实现方案 |
|------|---------|
| 文档分片 | overlap 分片，chunk=500，overlap=100 |
| 向量化存储 | BGE 中文模型 + ChromaDB 持久化 |
| 检索优化 | HyDE（假设答案 → 向量化 → 检索） |
| 问题改写 | 结合 history 补全模糊问题 |
| 多轮对话 | 超过10轮自动压缩历史摘要 |
| 来源追溯 | 显示笔记ID + 相似度 + 预览 |

核心流程：
```
问题改写 → HyDE生成假设答案 → 向量化 → 检索 → 组装prompt → LLM回答
```

### ✅ 2. Agent 系统（week6/day5/agent.py）

- Function Calling：`ask_rag` + `add_note` 两个工具
- ReAct 循环：工具调用 → 观察结果 → 继续决策
- 工具失败处理：try/except → 错误信息反馈给 LLM
- 行为边界控制：system prompt 限制回答范围
- 流式输出：SSE + 打字机效果

```python
# Agent 主循环
for step in range(max_steps):
    message = call_llm_with_tools(tools, history)
    if message.get("tool_calls"):
        # 执行工具 → 结果加入history
    else:
        # 流式返回最终答案
```

### ✅ 3. 全栈交付

- FastAPI 后端（`/ask/stream`、`/add` 接口）
- React 前端（流式对话界面，打字机效果）
- `config.py` 统一配置管理

### ✅ 4. Transformer 原理

手写实现 Self-Attention + Multi-Head Attention，能说清楚：

- QKV 原理、为什么除以 √d_k
- Multi-Head 意义、GPT vs BERT 区别
- 位置编码必要性

### ✅ 5. 系统设计

能回答「设计生产级 RAG 系统」：HNSW 索引、多租户隔离、语义缓存、监控体系

### ✅ 6. 评估体系

- 构建了 9 条评估数据集（坑记录）
- 有/无 HyDE 对比：75% vs **87.5%**（面试量化数据）

### ⚠️ 7. 推理优化（部分完成）

- KV Cache 原理（能说清楚）
- 流式输出（已实现）
- 量化/vLLM（了解概念，未实操）

---

## 文件结构

```
week6/day5/
├── config.py          # 统一配置
├── rag.py             # RAG核心逻辑
├── agent.py           # Agent + 工具调用
├── api.py             # FastAPI后端（uvicorn api:app --reload）
├── eval.py            # 评估脚本
├── train.json         # 微调数据集（48条）
├── train.py           # QLoRA训练脚本（待在Colab跑）
├── transation.py      # ChromaDB → train.json 转换脚本
├── chroma_db/         # 向量数据库
└── frontend/          # React前端
```

---

## 下一步计划（按优先级）

```
1. 🔥 模型微调（QLoRA）← 当前阶段
   - [ ] 在 Google Colab 跑 train.py 完整训练
   - [ ] 了解训练监控（loss曲线、过拟合判断）
   - [ ] 保存并加载 LoRA 权重推理

2. Multi-Agent 编排
   - [ ] 多个Agent协作
   - [ ] 角色分工设计（CrewAI / LangGraph）

3. MCP 协议
   - [ ] 了解原理
   - [ ] 接入外部工具

4. 最终模拟面试（全流程）
```

---

## 面试准备状态

| 项目 | 状态 |
|------|------|
| 项目讲述 | ✅ 能讲清楚 |
| 技术深度 | ✅ HyDE/ReAct/KV Cache 能说原理 |
| 系统设计 | ✅ 有完整框架 |
| 量化数据 | ✅ 87.5% 准确率 |
| 算法 | ✅ 滑动窗口写过 |
| 自我介绍 | ⚠️ 需要练习流畅度 |

---

## 给新对话的教学说明

```
你是我的 AGI 开发导师（字节/阿里/腾讯 8年经验 + 200+场面试官）。

我的背景：前端转AGI，已完成 RAG系统 + Agent系统 + 全栈交付，正在学习模型微调。

教学原则：
- 先写代码，遇到问题再讲原理
- 每个概念用「三层追问」问透
- 所有知识点都要在项目里有对应实现
- 遇到 bug 先引导我自己定位，不要直接给答案
- 每次回答末尾出一道延伸思考题

当前任务：[在此处填写今天要学的内容]
```
