import json
import os
import sys
import logging
from datetime import datetime

from state import PipelineState

logger = logging.getLogger(__name__)


def _load_image_generator(project_root: str):
    """动态加载项目中的图片生成器。"""
    art_tools_dir = os.path.join(project_root, "art", "tools")
    if art_tools_dir not in sys.path:
        sys.path.insert(0, art_tools_dir)
    from free_image_generator import PollinationsImageGenerator

    return PollinationsImageGenerator


def art_fix_node(state: PipelineState) -> dict:
    """美术修复节点：根据代码预检反馈，用 Python 重新生成失败的资源。

    1. 读取当前 manifest + code_questions（失败列表）
    2. 从 refined JSON 中找到对应资源的 prompt
    3. Python 循环调 Pollinations API 重新生成
    4. 合并生成新 manifest
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    new_manifest_path = f"pipeline/outputs/art/manifest/art_manifest_{ts}.json"
    os.makedirs(os.path.join(root, "pipeline/outputs/art/manifest"), exist_ok=True)

    # 读取当前 manifest
    manifest_file = os.path.join(root, state["latest"]["art"]["manifest"])
    with open(manifest_file, "r", encoding="utf-8") as f:
        old_manifest = json.load(f)

    # 读取失败列表
    questions_file = os.path.join(root, state["latest"]["code"]["questions"])
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)

    failed_ids = {issue["id"] for issue in questions.get("issues", [])}
    logger.info(f"需要修复 {len(failed_ids)} 个资源: {failed_ids}")

    # 读取 refined JSON 获取 prompt 信息
    refined_data = {}
    if state["latest"]["art"].get("refined"):
        refined_file = os.path.join(root, state["latest"]["art"]["refined"])
        if os.path.exists(refined_file):
            with open(refined_file, "r", encoding="utf-8") as f:
                refined = json.load(f)
            refined_data = {a["id"]: a for a in refined.get("assets", [])}

    # 加载图片生成器
    GeneratorClass = _load_image_generator(root)
    gen = GeneratorClass()

    # 逐个修复失败资源
    new_assets = []
    fix_count = 0
    fix_success = 0

    for old_asset in old_manifest["assets"]:
        if old_asset["id"] not in failed_ids:
            # 保留成功的条目不变
            new_assets.append(old_asset)
            continue

        fix_count += 1
        asset_id = old_asset["id"]

        # 从 refined 中获取完整信息
        refined_asset = refined_data.get(asset_id, {})
        prompt = refined_asset.get("prompt", old_asset.get("prompt_used", ""))
        width = refined_asset.get("width", 512)
        height = refined_asset.get("height", 512)
        category = refined_asset.get("category", "item")

        save_dir = os.path.join(root, f"pipeline/outputs/art/assets/{category}")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, f"{asset_id}_{ts}.png")
        rel_path = os.path.relpath(save_path, root).replace("\\", "/")

        logger.info(
            f"[修复 {fix_count}/{len(failed_ids)}] {asset_id} ({width}x{height})"
        )

        # 生成，支持 1 次重试
        result = gen.generate(
            prompt=prompt, width=width, height=height, save_path=save_path
        )
        if not result:
            result = gen.generate(
                prompt=prompt, width=width, height=height, save_path=save_path
            )

        status = "success" if result else "failed"
        if result:
            fix_success += 1
        logger.info(f"  -> {status}")

        new_assets.append(
            {
                "id": asset_id,
                "file_path": rel_path,
                "prompt_used": prompt,
                "size": f"{width}x{height}",
                "status": status,
            }
        )

    # 写入新 manifest
    success_total = sum(1 for a in new_assets if a["status"] == "success")
    failed_total = sum(1 for a in new_assets if a["status"] != "success")

    new_manifest = {
        "generated_at": datetime.now().isoformat(),
        "assets": new_assets,
        "summary": {
            "total": len(new_assets),
            "success": success_total,
            "failed": failed_total,
        },
    }

    manifest_full_path = os.path.join(root, new_manifest_path)
    with open(manifest_full_path, "w", encoding="utf-8") as f:
        json.dump(new_manifest, f, indent=2, ensure_ascii=False)

    logger.info(f"修复完成: {fix_success}/{fix_count} 成功")

    # 更新 latest 索引
    latest = state["latest"].copy()
    latest["art"]["manifest"] = new_manifest_path

    with open(
        os.path.join(root, "pipeline/outputs/latest.json"), "w", encoding="utf-8"
    ) as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {"current_phase": "art_fix_done", "latest": latest}
