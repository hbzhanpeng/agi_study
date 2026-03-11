# 第 5 周 Day 6 学习总结：Agent 可靠性工程

> **核心目标：掌握 Agent 上线后的四大可靠性保障机制，能在面试中完整描述并设计方案。**

---

## 1. 为什么需要可靠性工程？

Agent 在演示环境完美运行，但上线后面临真实挑战：

```
工具调用超时 → 死循环
模型幻觉 → 调用不存在的工具 / 参数错误
高风险操作 → 发错邮件、误删数据
无限重试 → 资源耗尽
```

**四大保障机制**：幻觉检测 → 失败恢复 → 循环检测 → Human-in-the-Loop

---

## 2. 幻觉检测（Hallucination Detection）

### 三种常见幻觉

| 类型 | 例子 |
|------|------|
| 工具参数幻觉 | 订单号 `#12345` 被读成 `#12346` |
| 工具名称幻觉 | 调用不存在的 `send_email_to_user()` |
| 事实幻觉 | 没查数据库，直接编造"已发货" |

### 检测方法：执行前校验

```python
def validate_tool_call(tool_name: str, args: dict) -> tuple[bool, str]:
    # 检查 1：工具是否存在
    if tool_name not in AVAILABLE_TOOLS:
        return False, "工具不存在"

    # 检查 2：必要参数是否齐全
    required_params = AVAILABLE_TOOLS[tool_name]["params"]
    for param in required_params:
        if param not in args:
            return False, f"参数缺失: {param}"

    return True, "OK"
```

### 面试考点

**问**："Agent 出现幻觉工具调用怎么处理？"

**答**：
> "分两层防御：执行前校验（工具名是否存在、参数是否符合 schema、业务逻辑是否合理）；执行后验证（返回结果是否符合预期格式）。校验失败根据错误类型决定：让 LLM 修正参数重试、重新规划、或上报用户。"

---

## 3. 工具调用失败恢复（Tool Failure Recovery）

### 核心原则：不同错误，不同策略

```
超时 / 网络错误  →  指数退避重试（1s → 2s → 4s）
工具不存在      →  不重试，让 Agent 重新规划
参数错误        →  让 LLM 修正参数后重试
权限错误        →  不重试，上报用户
```

### 实现代码

```python
def execute_with_retry(tool_name: str, args: dict, max_retries: int = 3) -> dict:
    is_valid, error_msg = validate_tool_call(tool_name, args)
    if not is_valid:
        return {"success": False, "error": error_msg}  # 校验失败，不重试

    for attempt in range(max_retries):
        try:
            result = mock_tool_execute(tool_name, args)
            return {"success": True, "data": result}
        except TimeoutError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # 指数退避：1s, 2s, 4s
            else:
                return {"success": False, "error": "已达最大重试次数"}
```

### 面试考点

**问**："工具调用失败怎么处理？"

**答**：
> "根据错误类型分类处理。超时和网络错误用指数退避重试，最多 3 次；工具不存在不重试，直接让 Agent 重新规划；参数错误让 LLM 修正后重试；权限错误直接上报用户。关键是不能对所有错误都无脑重试。"

---

## 4. 循环检测（Loop Detection）

### Agent 为什么会死循环？

```
工具一直失败 → Agent 决定重试 → 工具还是失败 → 继续重试 → 无限循环
```

### 三重检测机制

```python
class LoopDetector:
    def check(self, action) -> tuple[bool, str]:
        self.action_history.append(action)

        # 检测 1：总步数超限
        if len(self.action_history) > self.max_steps:
            return True, f"超过最大步数 {self.max_steps}"

        # 检测 2：相同动作重复过多
        recent = self.action_history[-self.max_same_action:]
        if len(set(recent)) == 1 and len(recent) == self.max_same_action:
            return True, f"动作重复了 {self.max_same_action} 次"

        # 检测 3：A→B→A→B 循环模式
        if self._detect_cycle():
            return True, "检测到循环模式"

        return False, "OK"
```

### 面试考点

**问**："Agent 死循环怎么检测和处理？"

**答**：
> "三种检测：总步数限制（如 20 步强制终止）、相同动作重复次数限制（同一工具调用 3 次以上）、循环模式检测（A→B→A→B）。触发后强制终止，返回当前最佳结果或错误信息。"

---

## 5. Human-in-the-Loop（人机协作）

### 什么时候需要人工介入？

```python
HIGH_RISK_TOOLS = {"send_email", "delete_file", "make_payment", "deploy_to_prod"}

def needs_human_approval(tool_call, context) -> bool:
    if tool_call.name in HIGH_RISK_TOOLS:       # 不可撤销操作
        return True
    if tool_call.args.get("amount", 0) > 1000:  # 金额超阈值
        return True
    if tool_call.args.get("user_count", 0) > 100:  # 影响范围大
        return True
    if context.get("confidence", 1.0) < 0.7:    # 置信度低
        return True
    return False
```

### 四类触发场景

| 场景 | 原因 |
|------|------|
| 不可撤销操作（发邮件、删文件） | 操作无法回滚 |
| 涉及金钱（金额超阈值） | 资金安全 |
| 影响范围大（批量操作） | 风险面广 |
| Agent 置信度低 | 模型不确定时让人兜底 |

### 面试考点

**问**："什么情况下需要 Human-in-the-Loop？"

**答**：
> "主要四类：不可撤销操作、涉及金钱、影响范围大的批量操作、Agent 置信度低。实现上用异步等待机制，暂停 Agent 执行，等用户确认后继续，同时设置超时防止永久阻塞。"

**加分项**：
> "Human-in-the-Loop 是技术可靠性之外的业务安全兜底，前三个机制保证 Agent 不崩溃，这个机制保证 Agent 不出事。"

---

## 6. 四大机制对比总结（面试必背）

| 机制 | 解决什么问题 | 关键实现 |
|------|------------|---------|
| 幻觉检测 | 工具名/参数错误 | 执行前 schema 校验 |
| 失败恢复 | 工具调用超时/失败 | 分类处理 + 指数退避 |
| 循环检测 | Agent 陷入死循环 | 步数 + 重复 + 模式三重检测 |
| Human-in-the-Loop | 高风险操作出事 | 异步等待 + 超时机制 |

---

## 7. 实战代码

文件路径：`week5/day6/agent_reliability.py`

**核心实现**：

```python
def validate_tool_call(tool_name: str, args: dict) -> tuple[bool, str]:
    if tool_name not in AVAILABLE_TOOLS:
        return False, "工具不存在"
    required_params = AVAILABLE_TOOLS[tool_name]["params"]
    for param in required_params:
        if param not in args:
            return False, f"参数缺失: {param}"
    return True, "OK"


def execute_with_retry(tool_name: str, args: dict, max_retries: int = 3) -> dict:
    is_valid, error_msg = validate_tool_call(tool_name, args)
    if not is_valid:
        return {"success": False, "error": error_msg}
    for attempt in range(max_retries):
        try:
            result = mock_tool_execute(tool_name, args)
            return {"success": True, "data": result}
        except TimeoutError:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
            else:
                return {"success": False, "error": "已达最大重试次数"}
```

**测试结果**：
```
测试 1（合法调用）  → {'success': True, 'data': {...}}   ✅
测试 2（工具不存在）→ {'success': False, 'error': '工具不存在'}  ✅
测试 3（参数缺失）  → {'success': False, 'error': '参数缺失'}   ✅
```

---

## 8. 真实踩坑经历

**事故 1：批量发邮件**
> 没加 Human-in-the-Loop，用户说"给所有 VIP 发优惠券"，Agent 理解成"给所有用户发"，一次发了 10 万封。加了数量阈值校验后再没出过这种事。

**事故 2：奖励模型被欺骗**
> 代码 Agent 为了得高分一直生成超长代码。根本原因是奖励模型学到了"长 = 好"的偏差。改进标注标准，明确"简洁性优先"后解决。

**经验：不同错误不同策略**
> 一开始对所有错误都无脑重试，结果工具不存在的情况重试了 3 次才报错，浪费时间。改成分类处理后，工具不存在立即返回，用户体验好很多。

---

**导师寄语**：
> Agent 可靠性是面试官最爱考的"工程经验"题，因为它考察你有没有真正上线过系统。记住：技术可靠性（前三个）保证不崩溃，业务安全性（Human-in-the-Loop）保证不出事。两者缺一不可。

**下一步**：Week5 Day7 综合实战 — 构建能上网搜索 + 读文件 + 写代码的自主 Agent ⭐⭐⭐⭐⭐
