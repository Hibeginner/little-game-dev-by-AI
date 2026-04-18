import os
import subprocess
import logging

logger = logging.getLogger(__name__)


def invoke_agent(
    model: str,
    prompt: str,
    workdir: str,
    files: list[str] | None = None,
    timeout: int = 600,
) -> str:
    """调用 CodeMaker CLI 非交互模式运行 Agent。

    注意：不使用 -f 参数（会导致位置参数被误判为文件路径）。
    而是在 prompt 中告知 Agent 需要读取的文件路径，
    依赖 CodeMaker 自身的文件读取能力。

    Args:
        model: 模型标识，如 "netease-codemaker/claude-opus-4-6"
        prompt: 发送给 Agent 的完整 prompt（应包含所有需要读取的文件路径）
        workdir: 工作目录（CodeMaker 在此目录下读写文件）
        files: 已弃用，仅用于日志（文件路径应直接写在 prompt 中）
        timeout: 超时秒数

    Returns:
        Agent 的 stdout 输出

    Raises:
        RuntimeError: CodeMaker 返回非零退出码
        subprocess.TimeoutExpired: 超时
    """
    cmd = ["codemaker", "run", "-m", model, prompt]

    logger.info(f"调用 Agent: model={model}, timeout={timeout}s")
    if files:
        logger.info(f"相关文件: {files}")
    logger.debug(f"Prompt 前 200 字: {prompt[:200]}...")

    try:
        result = subprocess.run(
            cmd,
            cwd=workdir,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )
        if result.returncode != 0:
            stderr_msg = (result.stderr or "")[:500]
            logger.error(f"Agent 返回非零退出码: {result.returncode}")
            logger.error(f"stderr: {stderr_msg}")
            raise RuntimeError(f"CodeMaker 退出码 {result.returncode}: {stderr_msg}")
        logger.info("Agent 调用成功")
        return result.stdout or ""
    except subprocess.TimeoutExpired:
        logger.error(f"Agent 超时 ({timeout}s)")
        raise
