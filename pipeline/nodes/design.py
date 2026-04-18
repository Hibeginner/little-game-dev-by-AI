import json
import os
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG


def design_node(state: PipelineState) -> dict:
    """策划设计节点：生成设计文档 + 美术需求清单。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    spec_path = f"pipeline/outputs/design/spec/design_spec_{ts}.md"
    art_req_path = (
        f"pipeline/outputs/design/art_requirements/art_requirements_{ts}.json"
    )

    os.makedirs(os.path.join(root, "pipeline/outputs/design/spec"), exist_ok=True)
    os.makedirs(
        os.path.join(root, "pipeline/outputs/design/art_requirements"), exist_ok=True
    )

    # 读取系统 prompt
    with open(
        os.path.join(root, "pipeline/prompts/design_system.md"), "r", encoding="utf-8"
    ) as f:
        system_prompt = f.read()

    # 如果是 reviewer 回退到 design，附带反馈
    review_context = ""
    if state.get("review_target") == "design" and state["latest"]["review"]["feedback"]:
        feedback_path = os.path.join(root, state["latest"]["review"]["feedback"])
        if os.path.exists(feedback_path):
            with open(feedback_path, "r", encoding="utf-8") as f:
                feedback = json.load(f)
            review_context = f"\n\n## Reviewer 反馈（请据此修订设计）\n{json.dumps(feedback['issues'], indent=2, ensure_ascii=False)}"

    prompt = f"""{system_prompt}

## 游戏概念

{state["game_concept"]}
{review_context}

## 输出路径

- 设计文档写入：{spec_path}
- 美术需求清单写入：{art_req_path}"""

    invoke_agent(
        model=NODE_CONFIG["design"]["model"],
        prompt=prompt,
        workdir=root,
        timeout=NODE_CONFIG["design"]["timeout"],
    )

    # 更新 latest 索引
    latest = state["latest"].copy()
    latest["design"]["spec"] = spec_path
    latest["design"]["art_requirements"] = art_req_path

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {"current_phase": "design_done", "latest": latest}
