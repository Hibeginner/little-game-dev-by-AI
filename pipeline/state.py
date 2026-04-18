from typing import TypedDict, Optional, Literal


class PipelineState(TypedDict):
    # 输入
    game_concept: str
    project_root: str

    # 运行控制
    run_id: str
    current_phase: str
    retry_count: int
    max_retries: int

    # Agent 间通信索引（latest.json 的内存镜像）
    latest: dict

    # 流程控制信号
    art_preflight_pass: bool
    code_preflight_pass: bool
    review_verdict: Optional[Literal["pass", "fail"]]
    review_target: Optional[Literal["design", "art", "code"]]

    # 终态
    status: Literal["running", "passed", "failed"]
    final_message: str
