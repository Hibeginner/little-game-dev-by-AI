import json
import os
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG


def design_clarify_node(state: PipelineState) -> dict:
    """策划澄清节点：回答美术 Agent 的提问。"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    answers_path = f"pipeline/outputs/design/art_answers/art_answers_{ts}.json"
    os.makedirs(
        os.path.join(root, "pipeline/outputs/design/art_answers"), exist_ok=True
    )

    spec_file = os.path.join(root, state["latest"]["design"]["spec"])
    questions_file = os.path.join(root, state["latest"]["art"]["questions"])

    prompt = f"""你是游戏策划，美术团队对你的需求清单有以下疑问。请逐一回答。

请阅读以下文件获取上下文：
- 设计文档：{state["latest"]["design"]["spec"]}
- 美术提问：{state["latest"]["art"]["questions"]}

请将回答写入：{answers_path}

回答格式（JSON）：
{{
  "answers": [
    {{
      "question_id": "对应提问中的 id",
      "answer": "你的回答",
      "updated_prompt_hint": "如需修正，提供更新后的英文 prompt（否则为 null）"
    }}
  ]
}}"""

    files_to_attach = [spec_file, questions_file]
    invoke_agent(
        model=NODE_CONFIG["design_clarify"]["model"],
        prompt=prompt,
        workdir=root,
        files=files_to_attach,
        timeout=NODE_CONFIG["design_clarify"]["timeout"],
    )

    # 更新 latest 索引
    latest = state["latest"].copy()
    latest["design"]["art_answers"] = answers_path

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {"current_phase": "design_clarify_done", "latest": latest}
