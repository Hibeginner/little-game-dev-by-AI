import json
import os
import sys
import logging
from datetime import datetime

from state import PipelineState
from agent import invoke_agent
from config import NODE_CONFIG

logger = logging.getLogger(__name__)


def _load_image_generator(project_root: str):
    """动态加载项目中的图片生成器（路径在项目根目录下）。"""
    art_tools_dir = os.path.join(project_root, "art", "tools")
    if art_tools_dir not in sys.path:
        sys.path.insert(0, art_tools_dir)
    from free_image_generator import PollinationsImageGenerator

    return PollinationsImageGenerator


def _generate_single_image(
    gen,
    asset: dict,
    save_path: str,
    max_retries: int = 2,
) -> str | None:
    """生成单张图片，支持重试。"""
    for attempt in range(1, max_retries + 1):
        result = gen.generate(
            prompt=asset["prompt"],
            width=asset["width"],
            height=asset["height"],
            save_path=save_path,
        )
        if result:
            return result
        if attempt < max_retries:
            logger.warning(f"  重试 ({attempt}/{max_retries})...")
    return None


def art_execute_node(state: PipelineState) -> dict:
    """美术执行节点：LLM 整理需求 → Python 逐个生图。

    Phase 1: 调用 LLM 整理美术需求（合并策划澄清、优化 prompt）
    Phase 2: 解析 refined JSON
    Phase 3: Python 循环调用 Pollinations API 逐张生成
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    refined_path = f"pipeline/outputs/art/refined/art_refined_{ts}.json"
    manifest_path = f"pipeline/outputs/art/manifest/art_manifest_{ts}.json"

    os.makedirs(os.path.join(root, "pipeline/outputs/art/refined"), exist_ok=True)
    os.makedirs(os.path.join(root, "pipeline/outputs/art/manifest"), exist_ok=True)
    for category in ["character", "background", "item", "effect", "ui"]:
        os.makedirs(
            os.path.join(root, f"pipeline/outputs/art/assets/{category}"), exist_ok=True
        )

    # ================================================================
    # Phase 1: LLM 整理需求
    # ================================================================
    logger.info("Phase 1: LLM 整理美术需求...")

    answers_context = ""
    if state["latest"]["design"].get("art_answers"):
        answers_file = os.path.join(root, state["latest"]["design"]["art_answers"])
        if os.path.exists(answers_file):
            answers_context = f"\n- 策划澄清回复：{state['latest']['design']['art_answers']}（请阅读此文件并合并修正内容）"

    refine_prompt = f"""你是美术总监。请阅读原始美术需求清单和策划澄清回复，整理出一份最终美术需求文件。

## 输入文件

- 原始美术需求清单：{state["latest"]["design"]["art_requirements"]}（请阅读此文件）
{answers_context}

## 整理要求

1. 合并策划澄清中的修正（如有）
2. 将 size 字段拆为 width（整数）和 height（整数）
3. 将每个 asset 的 prompt_hint 与整体 style 合并，生成最终英文 prompt
4. 追加风格一致性关键词：high quality, clean lines, consistent style
5. 删除 prompt_hint 和 size 字段，只保留新字段

## 输出格式

严格输出以下 JSON 格式到 {refined_path}，不要输出其他任何内容：

```json
{{
  "style_description": "整体美术风格的中文描述",
  "style_suffix": "统一追加的英文风格关键词",
  "assets": [
    {{
      "id": "唯一标识（snake_case）",
      "description": "中文描述",
      "category": "character | background | item | effect | ui",
      "width": 512,
      "height": 512,
      "prompt": "最终完整英文 prompt（含风格后缀）"
    }}
  ]
}}
```"""

    invoke_agent(
        model=NODE_CONFIG["art_execute"]["model"],
        prompt=refine_prompt,
        workdir=root,
        timeout=NODE_CONFIG["art_execute"]["timeout"],
    )

    # ================================================================
    # Phase 2: 解析 refined JSON
    # ================================================================
    logger.info("Phase 2: 解析 refined JSON...")

    refined_full_path = os.path.join(root, refined_path)
    if not os.path.exists(refined_full_path):
        raise FileNotFoundError(f"LLM 未生成 refined 文件: {refined_full_path}")

    with open(refined_full_path, "r", encoding="utf-8") as f:
        refined = json.load(f)

    assets = refined.get("assets", [])
    total = len(assets)
    logger.info(f"共 {total} 个资源待生成")

    # ================================================================
    # Phase 3: Python 逐个生图
    # ================================================================
    logger.info("Phase 3: 开始逐个生成图片...")

    GeneratorClass = _load_image_generator(root)
    gen = GeneratorClass()

    results = []
    success_count = 0
    failed_count = 0

    for i, asset in enumerate(assets, 1):
        asset_id = asset["id"]
        category = asset.get("category", "item")
        width = asset.get("width", 512)
        height = asset.get("height", 512)
        prompt = asset.get("prompt", "")

        save_dir = os.path.join(root, f"pipeline/outputs/art/assets/{category}")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{asset_id}_{ts}.png")
        rel_path = os.path.relpath(save_path, root).replace("\\", "/")

        logger.info(f"[{i}/{total}] {asset_id} ({width}x{height}) → {category}/")

        result_path = _generate_single_image(gen, asset, save_path)

        if result_path:
            status = "success"
            success_count += 1
            logger.info(f"  -> success")
        else:
            status = "failed"
            failed_count += 1
            logger.warning(f"  -> FAILED")

        results.append(
            {
                "id": asset_id,
                "file_path": rel_path,
                "prompt_used": prompt,
                "size": f"{width}x{height}",
                "status": status,
            }
        )

    # ================================================================
    # 写入 manifest
    # ================================================================
    manifest = {
        "generated_at": datetime.now().isoformat(),
        "assets": results,
        "summary": {
            "total": total,
            "success": success_count,
            "failed": failed_count,
        },
    }

    manifest_full_path = os.path.join(root, manifest_path)
    with open(manifest_full_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"Manifest 已写入: {manifest_path}")
    logger.info(f"结果: {success_count} 成功, {failed_count} 失败, 共 {total} 个")

    # ================================================================
    # 更新 latest 索引
    # ================================================================
    latest = state["latest"].copy()
    latest["art"]["refined"] = refined_path
    latest["art"]["manifest"] = manifest_path
    latest["art"]["assets"] = {
        cat: f"pipeline/outputs/art/assets/{cat}/"
        for cat in ["character", "background", "item", "effect", "ui"]
    }

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {"current_phase": "art_execute_done", "latest": latest}
