# tethered-trust (Python)

Fit, compatibility and recall checks for AI agents **before they buy**. Every answer is a decision (`supported`, `conditional`, `incompatible`, `insufficient_evidence`) with the rules checked, manufacturer sources and a signed receipt.

- Standard library only (Python 3.8+)
- Tool definitions for OpenAI, Anthropic and LangChain
- Same tools as the [Tethered Trust MCP server](https://tetheredtrust.com/agents) (`https://tetheredtrust.com/mcp`)

```sh
pip install tethered-trust            # add [langchain] for LangChain tools
```

## Quick start

```python
from tethered_trust import TetheredTrust

tt = TetheredTrust(sandbox=True)  # sandbox: free, never charged
cart = tt.check_cart({
    "owned": ["Sony PlayStation 5 Pro"],
    "line_items": [{"id": "li_1", "title": "Samsung 990 PRO with Heatsink 2TB", "quantity": 1}],
})
if cart["safe_to_checkout"]:
    # place the order, then link the receipt to it (free)
    tt.call("attach_order", {"receipt_id": cart["receipt"]["id"], "order_id": "112-5550001"})
else:
    print(cart["action"], cart["questions"])
```

Drop `sandbox=True` for live answers. Without a key you get a small free daily allowance; after that use an API key with prepaid credits (`TetheredTrust(api_key="tt_...")`, buy at [tetheredtrust.com/credits](https://tetheredtrust.com/credits)) or pay per answer in USDC with [x402](https://tetheredtrust.com/pricing).

## Give the tools to your model

```python
from openai import OpenAI
from tethered_trust import TetheredTrust, to_openai_tools, run_tool, SHOPPING_TOOLS

tt = TetheredTrust(api_key="tt_...")
res = OpenAI().chat.completions.create(
    model="gpt-4.1",
    messages=[{"role": "user", "content": "Will this charger work with my Pixel 10? Anker Nano Charger 30W"}],
    tools=to_openai_tools(SHOPPING_TOOLS),
)
for call in res.choices[0].message.tool_calls or []:
    print(run_tool(tt, call.function.name, call.function.arguments))
```

Anthropic: `to_anthropic_tools(SHOPPING_TOOLS)` gives the `tools` list for `client.messages.create(...)`; run each `tool_use` block with `run_tool(tt, block.name, block.input)`.

LangChain: `to_langchain_tools(tt, SHOPPING_TOOLS)` returns `StructuredTool`s you can bind to any chat model.

## What to do with the answer

| `decision` | Do this |
|---|---|
| `supported` | Proceed; relay caveats. |
| `conditional` | Proceed only once every item in `conditions` is met. |
| `incompatible` | Don't buy; use `substitutions` or `fix_purchase_plan`. |
| `insufficient_evidence` | Ask the returned `questions`, then check again. |

Keep the `receipt`; after ordering, `attach_order` makes it a [Decision Record](https://tetheredtrust.com/spec/decision-record). If an answer was wrong, `file_claim` within 60 days refunds the fee.

Docs: https://tetheredtrust.com/agents · Pricing: https://tetheredtrust.com/pricing · Terms: https://tetheredtrust.com/api-terms

Answers are informational; confirm with the manufacturer before buying. MIT licensed. © Chimes In LLC.
