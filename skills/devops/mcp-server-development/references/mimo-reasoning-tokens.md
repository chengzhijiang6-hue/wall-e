# MiMo Reasoning Model — Token Budget Behavior

## Problem
MiMo (mimo-v2.5-pro) is a reasoning model. It consumes `reasoning_tokens` FROM the `max_tokens` budget for internal chain-of-thought before producing visible output.

## Symptom
Setting `max_tokens=20` results in empty `content` field:
```
Content: []
Reasoning tokens: 19
Finish: length
```
All 20 tokens consumed by reasoning, 0 left for output.

## Solution
Always set `max_tokens >= 512` for MiMo calls. Recommended: 1024-2048 for wiki generation tasks.

```python
resp = client.chat.completions.create(
    model='mimo-v2.5-pro',
    messages=[{'role': 'user', 'content': '...'}],
    max_tokens=2048,  # Must be high enough for reasoning + output
)
```

## Diagnostic
Check `resp.usage.completion_tokens_details.reasoning_tokens` to see how many tokens went to reasoning vs output:
```python
reasoning = resp.usage.completion_tokens_details.reasoning_tokens
total = resp.usage.completion_tokens
visible = total - reasoning
```

## Embedding API Not Available on Token-Plan Endpoint

MiMo's token-plan endpoint (`https://token-plan-cn.xiaomimimo.com/v1`) does NOT support embedding models. Calling `client.embeddings.create()` returns 404.

**Workaround**: Use ChromaDB's built-in ONNX embedding function (default, no API key needed) or a separate embedding provider.

## General Rule for Reasoning Models
Any model with "reasoning" or "thinking" capabilities (MiMo, DeepSeek R1, QwQ, etc.) will consume tokens for internal reasoning. Always budget generously for `max_tokens`.
