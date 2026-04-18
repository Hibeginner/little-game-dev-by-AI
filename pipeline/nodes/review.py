import json
import os
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG


def review_node(state: PipelineState) -> dict:
    """功能审查节点：检查代码质量与设计一致性。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    feedback_path = f"pipeline/outputs/review/feedback/review_feedback_{ts}.json"
    os.makedirs(os.path.join(root, "pipeline/outputs/review/feedback"), exist_ok=True)

    # 读取系统 prompt
    with open(
        os.path.join(root, "pipeline/prompts/reviewer_system.md"), "r", encoding="utf-8"
    ) as f:
        system_prompt = f.read()

    spec_file = os.path.join(root, state["latest"]["design"]["spec"])
    manifest_file = os.path.join(root, state["latest"]["art"]["manifest"])

    prompt = f"""{system_prompt}

## 待审查文件

- 设计文档：{state["latest"]["design"]["spec"]}
- 美术资产清单：{state["latest"]["art"]["manifest"]}
- 项目代码目录：BabySleep/

请审查后将结果写入：{feedback_path}"""

    invoke_agent(
        model=NODE_CONFIG["review"]["model"],
        prompt=prompt,
        workdir=root,
        files=[spec_file, manifest_file],
        timeout=NODE_CONFIG["review"]["timeout"],
    )

    # 解析审查结果
    result_file = os.path.join(root, feedback_path)
    verdict = "fail"
    target = "code"
    try:
        if os.path.exists(result_file):
            with open(result_file, "r", encoding="utf-8") as f:
                feedback = json.load(f)
            verdict = feedback.get("verdict", "fail")
            target = feedback.get("target", "code")
    except (json.JSONDecodeError, KeyError):
        verdict = "fail"
        target = "code"

    # 更新 latest 索引
    latest = state["latest"].copy()
    latest["review"]["feedback"] = feedback_path

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    retry_count = state["retry_count"]
    if verdict == "fail":
        retry_count += 1

    return {
        "current_phase": "review_done",
        "review_verdict": verdict,
        "review_target": target,
        "retry_count": retry_count,
        "latest": latest,
    }
