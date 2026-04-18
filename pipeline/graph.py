from langgraph.graph import StateGraph, END
from state import PipelineState
from nodes.design import design_node
from nodes.art_preflight import art_preflight_node
from nodes.design_clarify import design_clarify_node
from nodes.art_execute import art_execute_node
from nodes.code_preflight import code_preflight_node
from nodes.art_fix import art_fix_node
from nodes.code_execute import code_execute_node
from nodes.review import review_node
from nodes.finalize import finalize_node


def route_art_preflight(state: PipelineState) -> str:
    """美术预检路由：有疑问则转策划澄清，否则直接执行生图。"""
    if state["art_preflight_pass"]:
        return "no_questions"
    return "has_questions"


def route_code_preflight(state: PipelineState) -> str:
    """代码预检路由：资源有问题则转美术修复，否则直接执行编码。"""
    if state["code_preflight_pass"]:
        return "no_issues"
    return "has_issues"


def route_review(state: PipelineState) -> str:
    """审查路由：通过则结束，未通过则根据 target 回退到对应 Agent。"""
    if state["review_verdict"] == "pass":
        return "pass"
    if state["retry_count"] >= state["max_retries"]:
        return "max_retries"
    target = state["review_target"]
    return f"retry_{target}"


def build_pipeline():
    """构建 LangGraph 状态机。"""
    graph = StateGraph(PipelineState)

    # 添加 9 个节点
    graph.add_node("design", design_node)
    graph.add_node("art_preflight", art_preflight_node)
    graph.add_node("design_clarify", design_clarify_node)
    graph.add_node("art_execute", art_execute_node)
    graph.add_node("code_preflight", code_preflight_node)
    graph.add_node("art_fix", art_fix_node)
    graph.add_node("code_execute", code_execute_node)
    graph.add_node("review", review_node)
    graph.add_node("finalize", finalize_node)

    # 入口
    graph.set_entry_point("design")

    # 固定边
    graph.add_edge("design", "art_preflight")
    graph.add_edge("design_clarify", "art_execute")  # 澄清后直接执行，不再预检
    graph.add_edge("art_execute", "code_preflight")
    graph.add_edge("art_fix", "code_execute")  # 修复后直接执行，不再预检
    graph.add_edge("finalize", END)

    # 条件边：美术预检
    graph.add_conditional_edges(
        "art_preflight",
        route_art_preflight,
        {"has_questions": "design_clarify", "no_questions": "art_execute"},
    )

    # 条件边：代码预检
    graph.add_conditional_edges(
        "code_preflight",
        route_code_preflight,
        {"has_issues": "art_fix", "no_issues": "code_execute"},
    )

    # 条件边：审查
    graph.add_conditional_edges(
        "review",
        route_review,
        {
            "pass": "finalize",
            "retry_design": "design",
            "retry_art": "art_execute",
            "retry_code": "code_execute",
            "max_retries": "finalize",
        },
    )

    return graph.compile()
