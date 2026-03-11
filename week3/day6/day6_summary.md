# 第 3 周 Day 6 学习总结：国产模型 API 对比与适配层封装

> **核心目标：掌握国产模型选型策略，能设计多模型适配层，在面试中说清楚选型理由。**

---

## 1. 为什么要了解国产模型？

```
现实情况：
- 国内企业项目，数据不能出境（金融/政务/医疗）
- OpenAI 价格贵，国产模型便宜 5-10 倍
- 中文场景，国产模型效果更好
- 部分场景需要私有化部署

面试场景：
- "你们项目用的什么模型？为什么选它？"
- "如果 OpenAI 涨价或者不可用，你怎么切换？"
- 这两个问题考察的是你的工程思维，不只是技术
```

---

## 2. 国产主流模型对比（面试必背）

| 模型 | 厂商 | 核心优势 | 适合场景 | 开源 |
|------|------|---------|---------|------|
| **DeepSeek** | DeepSeek | 代码极强、推理强、性价比最高 | 代码生成、逻辑推理 | ✅ |
| **Qwen（通义千问）** | 阿里 | 中文强、多模态、生态完整 | 电商/客服/通用 | ✅ |
| **GLM（智谱）** | 智谱 AI | 长文本、学术能力强 | 学术/长文档分析 | ✅ |
| **文心一言** | 百度 | 百度生态集成、搜索增强 | 搜索/知识问答 | ❌ |
| **豆包** | 字节 | 字节生态、多模态、性价比 | 内容创作/对话 | ❌ |

### 选型决策树

```
需要代码生成/推理？
  → DeepSeek（性价比最高，代码能力接近 GPT-4）

中文通用场景？
  → Qwen（阿里生态，中文效果最稳定）

长文档分析（>100K token）？
  → GLM-4（长文本窗口支持好）

需要私有化部署？
  → DeepSeek / Qwen（都有开源版本）

快速上线，不想运维？
  → 各家 API 都行，看价格和效果
```

---

## 3. 国产 vs OpenAI 对比

| 维度 | OpenAI GPT-4 | 国产顶级模型 |
|------|-------------|------------|
| 英文效果 | ✅ 最强 | 略逊 |
| 中文效果 | 好 | ✅ 更好（Qwen/DeepSeek） |
| 代码能力 | ✅ 强 | ✅ DeepSeek 接近 |
| 价格 | 贵（$30/1M tokens） | ✅ 便宜 5-10 倍 |
| 数据合规 | ❌ 数据出境风险 | ✅ 数据留国内 |
| 私有化部署 | ❌ 不支持 | ✅ 开源版本可部署 |
| API 稳定性 | ✅ 稳定 | 部分有波动 |

**面试加分点**：
> "我们项目选 DeepSeek 而不是 OpenAI，主要有三个原因：一是成本，DeepSeek 便宜约 8 倍；二是合规，客户数据不能出境；三是代码生成效果，DeepSeek 在我们的 benchmark 上和 GPT-4 差距很小。"

---

## 4. 适配层设计（适配器模式）

**核心问题**：业务代码直接调用某个模型的 SDK，换模型时要改很多地方。

**解决方案**：抽象一个统一接口，所有模型都实现这个接口。

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class BaseLLM(ABC):
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        pass


class OpenAILLM(BaseLLM):
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        from openai import OpenAI
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def chat(self, messages, **kwargs) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            **kwargs
        )
        return resp.choices[0].message.content

    def get_model_name(self) -> str:
        return self.model


class DeepSeekLLM(BaseLLM):
    def __init__(self, api_key: str):
        import requests
        self.api_key = api_key
        self.base_url = "https://api.deepseek.com/v1"

    def chat(self, messages, **kwargs) -> str:
        import requests
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": "deepseek-chat", "messages": messages, **kwargs}
        )
        return resp.json()["choices"][0]["message"]["content"]

    def get_model_name(self) -> str:
        return "deepseek-chat"


class QwenLLM(BaseLLM):
    def chat(self, messages, **kwargs) -> str:
        # 通义千问 API 实现
        pass

    def get_model_name(self) -> str:
        return "qwen-max"
```

### 工厂函数 + 配置驱动

```python
def get_llm(provider: str, **kwargs) -> BaseLLM:
    providers = {
        "openai": OpenAILLM,
        "deepseek": DeepSeekLLM,
        "qwen": QwenLLM,
    }
    if provider not in providers:
        raise ValueError(f"不支持的模型: {provider}")
    return providers[provider](**kwargs)

# 业务代码：一行切换模型
llm = get_llm("deepseek", api_key="xxx")
response = llm.chat([{"role": "user", "content": "你好"}])
```

---

## 5. Fallback 机制（生产必备）

**问题**：主模型挂了或限流，用户请求失败。

**解决**：自动切换到备用模型。

```python
class LLMWithFallback:
    def __init__(self, primary: BaseLLM, fallbacks: List[BaseLLM]):
        self.primary = primary
        self.fallbacks = fallbacks

    def chat(self, messages, **kwargs) -> str:
        models = [self.primary] + self.fallbacks

        for model in models:
            try:
                result = model.chat(messages, **kwargs)
                return result
            except Exception as e:
                print(f"[{model.get_model_name()}] 失败: {e}，切换备用...")
                continue

        raise RuntimeError("所有模型均不可用")

# 使用
llm = LLMWithFallback(
    primary=get_llm("openai", api_key="xxx"),
    fallbacks=[
        get_llm("deepseek", api_key="yyy"),
        get_llm("qwen", api_key="zzz"),
    ]
)
```

---

## 6. 面试考点汇总

### 问法 1："你们项目为什么选 XX 模型？"

**标准答案框架**：
> "我们从三个维度评估：效果（在我们的测试集上 benchmark）、成本（token 价格 × 日均用量）、合规（数据是否能出境）。最终选了 [模型名]，因为 [具体原因]。"

### 问法 2："如何设计一个支持多模型切换的系统？"

**标准答案**：
> "用适配器模式，抽象一个 BaseLLM 接口，所有模型实现同一套 chat() 方法。业务代码只依赖接口，不依赖具体实现。切换模型只需改配置文件，不需要改业务代码。生产环境还要加 Fallback 机制，主模型挂了自动切备用。"

### 问法 3："国产模型和 OpenAI 怎么选？"

**标准答案**：
> "看三个因素：数据合规（国内敏感行业必须用国产）、成本（国产便宜 5-10 倍）、效果（中文场景国产更好，英文和复杂推理 OpenAI 更强）。我们通常的策略是：先用 OpenAI 快速验证，上线前做 benchmark 对比，能用国产替换的就替换。"

**加分项**：
- 能说出 Fallback 机制的设计
- 能说出"在自己数据集上 benchmark，不看排行榜选模型"

---

## 7. 真实踩坑经历

**坑 1：直接调 SDK 导致换模型改了 30 个文件**
> 早期直接用 `openai.ChatCompletion.create()`，后来要切换到国产模型，发现 30 多个文件都有这个调用，改了整整一天。后来抽了适配层，再换模型只改一行配置。

**坑 2：没有 Fallback，凌晨 OpenAI 限流导致服务中断**
> 凌晨 2 点 OpenAI 限流，所有请求失败，用户投诉。加了 Fallback 到 DeepSeek 后，主模型挂了自动切换，用户无感知。

**坑 3：不同模型的 system prompt 效果差异大**
> 同一个 system prompt，在 GPT-4 上效果很好，切到 Qwen 后输出格式完全不同。后来针对每个模型单独调优 system prompt，适配层里加了 `get_system_prompt(model_name)` 方法。

---

**导师寄语**：
> 国产模型这个话题在面试中越来越重要，因为大多数国内公司都在用国产模型。记住：选型要说出理由（效果/成本/合规），设计要说出适配器模式，生产要说出 Fallback 机制。这三点能说清楚，这道题就满分了。

**下一步**：Week3 Day7 — 综合复习 + 实战项目
