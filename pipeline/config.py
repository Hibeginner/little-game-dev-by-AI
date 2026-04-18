from enum import Enum


class Model(str, Enum):
    CLAUDE_OPUS = "netease-codemaker/claude-opus-4-6"
    QWEN_36_PLUS = "netease-codemaker/qwen3.6-plus"


NODE_CONFIG = {
    "design": {"model": Model.QWEN_36_PLUS.value, "timeout": 600},
    "art_preflight": {"model": Model.QWEN_36_PLUS.value, "timeout": 300},
    "design_clarify": {"model": Model.QWEN_36_PLUS.value, "timeout": 600},
    "art_execute": {"model": Model.QWEN_36_PLUS.value, "timeout": 300},
    "code_execute": {"model": Model.QWEN_36_PLUS.value, "timeout": 1200},
    "review": {"model": Model.QWEN_36_PLUS.value, "timeout": 300},
}
