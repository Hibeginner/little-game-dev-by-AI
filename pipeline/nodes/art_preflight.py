import json
import os
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG


def art_preflight_node(state: PipelineState) -> dict:
    """美术预检节点：检查需求清单是否清晰完整。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    art_req_file = os.path.join(root, state["latest"]["design"]["art_requirements"])
    questions_path = f"pipeline/outputs/art/questions/art_questions_{ts}.json"
    os.makedirs(os.path.join(root, "pipeline/outputs/art/questions"), exist_ok=True)

    prompt = f"""你是美术总监，请审阅附带的美术需求清单，检查以下问题：

1. 是否有描述不清、无法理解的条目？
2. 是否有互相矛盾的需求（如风格冲突、尺寸不合理）？
3. 是否有明显遗漏的必要资源？

如果没有任何问题，请将以下 JSON 写入 {questions_path}：
{{"status": "pass", "questions": []}}

如果有问题，请将以下格式的 JSON 写入 {questions_path}：
{{
  "status": "has_questions",
  "questions": [
    {{
      "id": "问题编号（如 q1, q2）",
      "asset_id": "相关资源 ID（如有，否则为 null）",
      "question": "你的问题（中文）"
    }}
  ]
}}"""

    invoke_agent(
        model=NODE_CONFIG["art_preflight"]["model"],
        prompt=prompt,
        workdir=root,
        files=[art_req_file],
        timeout=NODE_CONFIG["art_preflight"]["timeout"],
    )

    # 读取预检结果
    result_file = os.path.join(root, questions_path)
    has_questions = False
    if os.path.exists(result_file):
        try:
            with open(result_file, "r", encoding="utf-8") as f:
                result = json.load(f)
            has_questions = result.get("status") == "has_questions"
        except (json.JSONDecodeError, KeyError):
            has_questions = False

    # 更新 latest 索引
    latest = state["latest"].copy()
    if has_questions:
        latest["art"]["questions"] = questions_path

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {
        "art_preflight_pass": not has_questions,
        "current_phase": "art_preflight_done",
        "latest": latest,
    }
