import pydevd_pycharm

pydevd_pycharm.settrace(
    "localhost", port=37211, stdout_to_server=True, stderr_to_server=True
)

import argparse
import json
import logging
import os
import sys
from datetime import datetime

from graph import build_pipeline
from state import PipelineState


def setup_logging(level: str = "INFO"):
    """配置日志格式。"""
    logging.basicConfig(
        level=getattr(logging, level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def run_pipeline(game_concept: str, project_root: str, max_retries: int = 3):
    """运行完整的游戏开发流水线。"""
    pipeline = build_pipeline()
    run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 确保 outputs 根目录存在
    os.makedirs(os.path.join(project_root, "pipeline/outputs"), exist_ok=True)

    initial_state: PipelineState = {
        "game_concept": game_concept,
        "project_root": project_root,
        "run_id": run_id,
        "current_phase": "init",
        "retry_count": 0,
        "max_retries": max_retries,
        "latest": {
            "design": {"spec": None, "art_requirements": None, "art_answers": None},
            "art": {"questions": None, "refined": None, "manifest": None, "assets": {}},
            "code": {"questions": None, "project_dir": "BabySleep/"},
            "review": {"feedback": None},
        },
        "art_preflight_pass": True,
        "code_preflight_pass": True,
        "review_verdict": None,
        "review_target": None,
        "status": "running",
        "final_message": "",
    }

    # 写入初始 latest.json
    latest_path = os.path.join(project_root, "pipeline/outputs/latest.json")
    with open(latest_path, "w", encoding="utf-8") as f:
        json.dump(initial_state["latest"], f, indent=2, ensure_ascii=False)

    logging.info(f"Pipeline 启动: run_id={run_id}")
    logging.info(f"项目根目录: {project_root}")
    logging.info(f"最大重试次数: {max_retries}")
    logging.info(f"游戏概念: {game_concept[:100]}...")

    final_state = pipeline.invoke(initial_state)

    logging.info(f"Pipeline 完成: {final_state['status']}")
    print(f"\n{'=' * 60}")
    print(final_state["final_message"])
    print(f"{'=' * 60}")

    return final_state


def main():
    parser = argparse.ArgumentParser(
        description="LangGraph 游戏开发流水线",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python -m pipeline.main "一款休闲反应力游戏，玩家需要哄宝宝睡觉"
  python -m pipeline.main concept.txt --max-retries 5
  python3 main.py "扫雷.txt" --project-root D:/little-game --log-level DEBUG
        """,
    )
    parser.add_argument("concept", help="游戏概念描述（字符串或文件路径）")
    parser.add_argument(
        "--project-root",
        default=os.getcwd(),
        help="项目根目录（默认当前目录）",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Reviewer 最大重试次数（默认 3）",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认 INFO）",
    )
    args = parser.parse_args()

    setup_logging(args.log_level)

    # 支持从文件读取游戏概念
    if os.path.isfile(args.concept):
        with open(args.concept, "r", encoding="utf-8") as f:
            concept = f.read()
        logging.info(f"从文件读取游戏概念: {args.concept}")
    else:
        concept = args.concept

    run_pipeline(concept, args.project_root, args.max_retries)


if __name__ == "__main__":
    main()
