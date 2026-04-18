import json
import os
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG


def code_execute_node(state: PipelineState) -> dict:
    """代码编写节点：生成 Cocos Creator 项目代码。"""
    root = state["project_root"]

    # 读取系统 prompt
    with open(
        os.path.join(root, "pipeline/prompts/code_system.md"), "r", encoding="utf-8"
    ) as f:
        system_prompt = f.read()

    spec_file = os.path.join(root, state["latest"]["design"]["spec"])
    manifest_file = os.path.join(root, state["latest"]["art"]["manifest"])

    files_to_attach = [spec_file, manifest_file]

    # 如果是 reviewer 回退到 code，附带反馈
    review_context = ""
    if state.get("review_target") == "code" and state["latest"]["review"]["feedback"]:
        feedback_file = os.path.join(root, state["latest"]["review"]["feedback"])
        if os.path.exists(feedback_file):
            files_to_attach.append(feedback_file)
            review_context = f"\n\n## Reviewer 反馈（请据此修复代码）\n请阅读：{state['latest']['review']['feedback']}"

    prompt = f"""{system_prompt}

## 输入文件

- 设计文档：{state["latest"]["design"]["spec"]}
- 美术资产清单：{state["latest"]["art"]["manifest"]}
{review_context}

## 输出

将所有代码写入 BabySleep/ 目录，遵循设计文档中定义的目录结构。"""

    invoke_agent(
        model=NODE_CONFIG["code_execute"]["model"],
        prompt=prompt,
        workdir=root,
        files=files_to_attach,
        timeout=NODE_CONFIG["code_execute"]["timeout"],  # 20分钟：创建完整 Cocos 项目需要较长时间
    )

    return {"current_phase": "code_execute_done"}
