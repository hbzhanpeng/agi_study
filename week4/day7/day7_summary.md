# 第 4 周 Day 7 学习总结：综合复习 + RAG 大实战

> **核心目标：整合全周知识，构建完整的智能文档问答系统。**

---

## 1. 综合复习成绩

**6/6 全对！** 覆盖 RAG 核心架构、Chunking、Embedding 选型、检索策略、HyDE、评估体系。

---

## 2. RAG 大实战：智能文档问答系统

### 架构图
```
用户提问 → smart_route 路由判断
  ├── "direct" → LLM 直接回答（如 1+1=2）
  ├── "rewrite" → Query 改写 → 向量检索 → RAG 生成
  └── "normal" → 向量检索 → RAG 生成
                                    ↓
                    检索到的文档 + 问题 → LLM 回答
                                    ↓
                              evaluate 自动评估
```

### 三个核心 TODO 实现

**TODO 1: 智能路由**
```python
def smart_route(question):
    if any(kw in question for kw in company_keywords):
        return "normal"
    if any(kw in question for kw in casual_markers):
        return "rewrite"
    return "direct"
```

**TODO 2: 完整问答管线**
- 路由判断 → 条件分支处理 → 检索 → RAG Prompt → 回答

**TODO 3: 批量评估**
- 遍历测试集 → 调用 ask → 检查 expected_answer → 统计准确率

### 运行结果
```
6/6 = 100% 全部命中
```

---

## 3. 本周踩坑总结

| 踩坑 | 教训 |
|------|------|
| .env 路径 | `__file__` 目录不等于项目根目录 |
| f-string 忘加 f | `"""` 和 `f"""` 差别巨大 |
| answer 是字符串不是列表 | 搞清楚变量类型再写代码 |
| RAG Prompt 允许瞎编 | ⚠️ 必须加"不确定就说不知道" |
| 路由顺序影响结果 | normal 判断在 rewrite 之前 |

---

## 4. 第 4 周完整收获

```
Day 1: RAG 核心架构（三阶段）
Day 2: Chunking 策略（递归分块）
Day 3: Embedding + 向量数据库选型
Day 4: 检索策略 + RAG 完整实战 ✅
Day 5: Query 改写 + HyDE 实战 ✅
Day 6: RAG 评估体系 + 自动评估 ✅
Day 7: 综合复习 + 智能问答系统 ✅
```

---

## 5. 下一步学习

**第 5 周**：AI Agent（智能体）
