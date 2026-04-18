import json
import os
from datetime import datetime

from state import PipelineState


def code_preflight_node(state: PipelineState) -> dict:
    """纯 Python 预检：检查美术资源完整性。

    检查项：
    - 文件是否存在
    - 文件是否为空
    - manifest 中的 status 是否为 success
    """
    root = state["project_root"]
    manifest_path = os.path.join(root, state["latest"]["art"]["manifest"])

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    issues = []
    for asset in manifest["assets"]:
        file_path = os.path.join(root, asset["file_path"])

        # 检查文件是否存在
        if not os.path.exists(file_path):
            issues.append(
                {
                    "id": asset["id"],
                    "issue": "文件不存在",
                    "path": asset["file_path"],
                }
            )
            continue

        # 检查文件大小（空文件视为失败）
        if os.path.getsize(file_path) == 0:
            issues.append(
                {
                    "id": asset["id"],
                    "issue": "文件为空",
                    "path": asset["file_path"],
                }
            )

        # 检查生成状态
        if asset.get("status") != "success":
            issues.append(
                {
                    "id": asset["id"],
                    "issue": f"状态异常: {asset.get('status')}",
                    "path": asset["file_path"],
                }
            )

    if issues:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        questions_dir = os.path.join(root, "pipeline/outputs/code/questions")
        os.makedirs(questions_dir, exist_ok=True)
        questions_path = f"pipeline/outputs/code/questions/code_questions_{ts}.json"

        with open(os.path.join(root, questions_path), "w", encoding="utf-8") as f:
            json.dump(
                {"issues": issues, "request": "请重新生成以下失败的资源"},
                f,
                indent=2,
                ensure_ascii=False,
            )

        latest = state["latest"].copy()
        latest["code"]["questions"] = questions_path

        return {
            "code_preflight_pass": False,
            "latest": latest,
            "current_phase": "code_preflight_fail",
        }

    return {"code_preflight_pass": True, "current_phase": "code_preflight_pass"}
