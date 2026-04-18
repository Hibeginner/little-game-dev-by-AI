"""单独测试后半段 pipeline：code_preflight → code_execute → review → finalize"""

import json
import os
import logging

from nodes.code_preflight import code_preflight_node
from nodes.code_execute import code_execute_node
from nodes.review import review_node
from nodes.finalize import finalize_node

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

root = r"D:\little-game"

# 从 latest.json 加载当前状态
with open(
    os.path.join(root, "pipeline/outputs/latest.json"), "r", encoding="utf-8"
) as f:
    latest = json.load(f)

state = {
    "game_concept": "Baby Sleep game",
    "project_root": root,
    "run_id": "20260417_213228",
    "current_phase": "art_execute_done",
    "retry_count": 0,
    "max_retries": 3,
    "latest": latest,
    "art_preflight_pass": True,
    "code_preflight_pass": True,
    "review_verdict": None,
    "review_target": None,
    "status": "running",
    "final_message": "",
}

# Step 1: code_preflight
print("\n=== CODE PREFLIGHT ===")
result = code_preflight_node(state)
state.update(result)
print(f"Result: preflight_pass={state['code_preflight_pass']}")

if not state["code_preflight_pass"]:
    print("Code preflight found issues, skipping to finalize")
    state["review_verdict"] = "fail"
    state["review_target"] = "art"
else:
    # Step 2: code_execute
    print("\n=== CODE EXECUTE ===")
    result = code_execute_node(state)
    state.update(result)
    print(f"Phase: {state['current_phase']}")

    # Step 3: review
    print("\n=== REVIEW ===")
    result = review_node(state)
    state.update(result)
    print(f"Verdict: {state['review_verdict']}, Target: {state['review_target']}")

# Step 4: finalize
print("\n=== FINALIZE ===")
result = finalize_node(state)
state.update(result)
print(f"\n{state['final_message']}")
