import json
import os
from datetime import datetime

from state import PipelineState


def finalize_node(state: PipelineState) -> dict:
    """生成最终运行报告并写入 meta/run_log/。

    纯 Python 节点，不调用 LLM。
    """
    root = state["project_root"]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    status = "passed" if state["review_verdict"] == "pass" else "failed"

    run_log = {
        "run_id": state["run_id"],
        "status": status,
        "finished_at": datetime.now().isoformat(),
        "retry_count": state["retry_count"],
        "max_retries": state["max_retries"],
        "final_outputs": {
            "design_spec": state["latest"]["design"]["spec"],
            "art_manifest": state["latest"]["art"]["manifest"],
            "project_dir": state["latest"]["code"]["project_dir"],
        },
        "review_feedback": state["latest"]["review"].get("feedback"),
    }

    log_dir = os.path.join(root, "pipeline/outputs/meta/run_log")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, f"run_log_{ts}.json")

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(run_log, f, indent=2, ensure_ascii=False)

    message = f"Pipeline {status}. 运行日志: {log_path}"
    if status == "failed":
        feedback_path = state["latest"]["review"].get("feedback")
        if feedback_path:
            message += f"\n最后一次审查反馈: {feedback_path}"

    return {
        "status": status,
        "final_message": message,
        "current_phase": "finalize",
    }
