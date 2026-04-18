# LangGraph 多 Agent 游戏开发流水线 — 设计文档

**日期：** 2026-04-17
**目标：** 构建一个可复用的 LangGraph 多 Agent 工作流，自动化完成"策划设计 → 美术资源生成 → 代码编写 → 功能审查"全流程，首个 demo 为 Baby Sleep 游戏。

---

## 一、项目概述

### 1.1 背景

当前 Baby Sleep 游戏已有完整的设计文档和 HTML 原型，但尚未开始 Cocos Creator 3.x 的正式实现。本项目通过 LangGraph 编排多个 AI Agent，将游戏从概念到成品的流程自动化。

### 1.2 核心价值

- **可复用**：不绑定 Baby Sleep，输入任意游戏概念即可驱动整条流水线
- **可追溯**：所有中间产物带时间戳存档，便于回溯调试
- **有反馈**：内置预检机制和 Reviewer 审查循环，质量可控

### 1.3 技术选型

| 层次 | 选型 | 说明 |
|------|------|------|
| 编排框架 | Python + LangGraph | StateGraph 管理工作流状态和路由 |
| Agent 运行时 | CodeMaker CLI (`codemaker run`) | 非交互模式，通过 subprocess 调用 |
| Agent 间通信 | 文件系统 + `latest.json` 索引 | Agent 读写约定路径的文件，编排器维护索引 |
| 图片生成 | Pollinations.ai（`free_image_generator.py`） | 免费，无需 API Key |
| 最终产出 | Cocos Creator 3.x 项目 | TypeScript + 生成的美术资源 |

---

## 二、整体架构

### 2.1 流程总览

```
                    ┌──────────────────────────────────────────┐
                    │                                          │
                    ▼                                          │
[START] → Design Agent → Art Agent → Code Agent → Reviewer ──┤
           (opus-4-6)   (qwen3.6+)   (opus-4-6)  (opus-4-6) │
                                                              │
                                                   PASS ──→ [END]
                                                   FAIL ──→ route back
                                                   (max 3 retries)
```

### 2.2 预检机制

每个下游 Agent 在正式执行前做一轮轻量级预检：

- **美术预检**：读取美术需求清单，检查是否有描述不清/矛盾/缺失的条目。有疑问则写提问文件，触发策划 Agent 澄清（限 1 次）。
- **代码预检**：读取美术资产清单，检查图片是否全部生成成功、格式尺寸是否正确。有问题则写提问文件，触发美术 Agent 修复（限 1 次）。

### 2.3 带预检的完整流程图

```
[START]
   │
   ▼
 design ──────────────────────────────────┐
   │                                      │
   ▼                                      │
 art_preflight                            │
   │                                      │
   ├─ 有疑问 → design_clarify ──┐         │
   │                            │         │
   │    ┌───────────────────────┘         │
   │    │                                 │
   │    ▼                                 │
   └─ 无疑问/已澄清                       │
   │                                      │
   ▼                                      │
 art_execute                              │
   │                                      │
   ▼                                      │
 code_preflight                           │
   │                                      │
   ├─ 有问题 → art_fix ──┐               │
   │                      │               │
   │    ┌─────────────────┘               │
   │    │                                 │
   │    ▼                                 │
   └─ 无问题/已修复                        │
   │                                      │
   ▼                                      │
 code_execute                             │
   │                                      │
   ▼                                      │
 review                                   │
   │                                      │
   ├─ pass → finalize → [END]            │
   │                                      │
   ├─ fail & retry < 3                    │
   │   ├─ target=design ─────────────────→┘ (回到 design)
   │   ├─ target=art ──→ art_execute
   │   └─ target=code ──→ code_execute
   │
   └─ fail & retry >= 3 → finalize → [END]（带错误报告）
```

---

## 三、Agent 调用机制

### 3.1 CodeMaker CLI 调用

每个 LangGraph 节点的核心都是通过 subprocess 调用 CodeMaker CLI：

```python
import subprocess

def invoke_agent(model: str, prompt: str, workdir: str, files: list[str] = None) -> str:
    cmd = ["codemaker", "run", "-m", model]
    if files:
        for f in files:
            cmd.extend(["-f", f])
    cmd.append(prompt)

    result = subprocess.run(
        cmd,
        cwd=workdir,
        capture_output=True,
        text=True,
        timeout=600
    )
    return result.stdout
```

### 3.2 调用参数

| 参数 | 选择 | 理由 |
|------|------|------|
| 工作目录 | 项目根目录 | CodeMaker 可以读写所有文件 |
| 超时 | 设计/代码 Agent: 600s, 美术 Agent: 900s, Reviewer: 300s | 美术 Agent 需要调用 Pollinations API |
| 输出格式 | `--format default` | stdout 用于日志，真正的数据通过文件传递 |
| 错误处理 | 非零退出码 → 重试一次，再失败 → pipeline 终止 | 简单可靠 |

### 3.3 Prompt 设计

每个 Agent 的 prompt 分两部分：

1. **系统指令**（从 `pipeline/prompts/*.md` 读取）：定义角色、职责、输出规范
2. **动态上下文**（Python 拼接）：当前游戏概念、上一步输出路径、reviewer 反馈等

编排器从 `latest.json` 获取上游输出路径，通过 `-f` 参数附带文件，并在 prompt 中明确指出输入和输出路径。Agent 不操作 `latest.json`，只负责按约定路径写文件，编排器负责登记。

---

## 四、Agent 职责与数据契约

### 4.1 策划设计 Agent（Design Agent）

| 项目 | 说明 |
|------|------|
| **模型** | `netease-codemaker/claude-opus-4-6` |
| **角色** | 游戏策划，将用户的游戏概念转化为结构化设计文档 |
| **输入** | 用户提供的游戏概念描述（字符串） |
| **输出** | `design/spec/design_spec_{ts}.md` — 完整游戏设计文档 |
| | `design/art_requirements/art_requirements_{ts}.json` — 美术需求清单 |

**`art_requirements.json` 格式：**

```json
{
  "style": "Q版卡通扁平风格，色彩温馨",
  "assets": [
    {
      "id": "baby_sleeping",
      "description": "Q版宝宝安睡状态，闭眼，脸颊红润，侧躺在枕头上",
      "category": "character",
      "size": "512x512",
      "prompt_hint": "cute chibi baby sleeping peacefully, rosy cheeks, side lying on pillow, warm colors, flat cartoon style"
    }
  ]
}
```

每个 asset 条目字段：

| 字段 | 说明 |
|------|------|
| `id` | 唯一标识 |
| `description` | 中文描述 |
| `category` | `character` / `background` / `item` / `effect` / `ui` |
| `size` | 尺寸，如 `"512x512"`, `"1024x576"` |
| `prompt_hint` | 给 Pollinations 的英文 prompt 建议 |

### 4.2 美术资源 Agent（Art Agent）

| 项目 | 说明 |
|------|------|
| **模型** | `netease-codemaker/qwen3.6-plus` |
| **角色** | 美术总监，根据需求清单生成全部图片资源 |
| **输入** | `art_requirements_{ts}.json` + `art_answers_{ts}.json`（如有） |
| **输出** | `art/assets/{category}/` 目录下的图片文件 |
| | `art/manifest/art_manifest_{ts}.json` — 生成结果清单 |

**工作流程：**

1. 读取 `art_requirements.json`
2. 对每个 asset，优化 `prompt_hint`（加入风格一致性描述）
3. 调用 `python art/tools/free_image_generator.py` 生成图片
4. 将结果写入 `art_manifest.json`

**`art_manifest.json` 格式：**

```json
{
  "generated_at": "2026-04-17T10:30:00",
  "assets": [
    {
      "id": "baby_sleeping",
      "file_path": "pipeline/outputs/art/assets/character/baby_sleeping_20260417_110000.png",
      "prompt_used": "cute chibi baby sleeping peacefully...",
      "size": "512x512",
      "status": "success"
    }
  ],
  "summary": { "total": 20, "success": 18, "failed": 2 }
}
```

### 4.3 代码编写 Agent（Code Agent）

| 项目 | 说明 |
|------|------|
| **模型** | `netease-codemaker/claude-opus-4-6` |
| **角色** | Cocos Creator 开发工程师 |
| **输入** | `design_spec_{ts}.md` + `art_manifest_{ts}.json` |
| **输出** | `BabySleep/` 目录下的完整 Cocos Creator 项目文件 |

**职责范围：**

- 创建 Cocos Creator 项目目录结构
- 编写所有 TypeScript 脚本（GameManager、LevelController、事件系统等）
- 配置数据表（EventConfig、LevelConfig）
- 将生成的图片资源复制/引用到正确的 `textures/` 目录
- 创建基本的场景描述文件

### 4.4 功能 Reviewer

| 项目 | 说明 |
|------|------|
| **模型** | `netease-codemaker/claude-opus-4-6` |
| **角色** | 技术审查员，检查代码质量与设计一致性 |
| **输入** | 全部输出文件（设计文档 + 资产清单 + 项目代码） |
| **输出** | `review/feedback/review_feedback_{ts}.json` |

**检查维度：**

1. **完整性** — 设计文档中的所有功能是否都有对应代码实现
2. **正确性** — TypeScript 代码是否有明显语法/逻辑错误
3. **资源引用** — 代码中引用的资源路径是否与 art_manifest 一致
4. **架构一致** — 代码结构是否符合设计文档中的架构规划

**`review_feedback.json` 格式：**

```json
{
  "verdict": "fail",
  "target": "code",
  "issues": [
    {
      "severity": "high",
      "file": "BabySleep/assets/scripts/events/DragEvent.ts",
      "description": "拖拽事件缺少触摸结束判定逻辑"
    }
  ],
  "summary": "代码基本完整，但有2个高优先级问题需要修复"
}
```

| 字段 | 说明 |
|------|------|
| `verdict` | `"pass"` 或 `"fail"` |
| `target` | `"design"` / `"art"` / `"code"` — 指示应该回退到哪个 Agent |
| `issues` | 问题列表，每项含 `severity`（high/medium/low）、`file`、`description` |
| `summary` | 一句话总结 |

最多 3 次重试，超过则终止并输出最终报告。

---

## 五、文档管理

### 5.1 目录结构

```
pipeline/outputs/
├── latest.json
├── design/
│   ├── spec/
│   │   ├── design_spec_20260417_103000.md
│   │   └── design_spec_20260417_113000.md
│   ├── art_requirements/
│   │   ├── art_requirements_20260417_103000.json
│   │   └── art_requirements_20260417_113000.json
│   └── art_answers/
│       └── art_answers_20260417_104500.json
├── art/
│   ├── questions/
│   │   └── art_questions_20260417_104000.json
│   ├── manifest/
│   │   ├── art_manifest_20260417_110000.json
│   │   └── art_manifest_20260417_120000.json
│   └── assets/
│       ├── character/
│       │   ├── baby_sleeping_20260417_110000.png
│       │   └── ...
│       ├── background/
│       │   └── ...
│       ├── item/
│       │   └── ...
│       ├── effect/
│       │   └── ...
│       └── ui/
│           └── ...
├── code/
│   └── questions/
│       └── code_questions_20260417_111500.json
├── review/
│   └── feedback/
│       ├── review_feedback_20260417_115000.json
│       └── review_feedback_20260417_130000.json
└── meta/
    └── run_log/
        └── run_log_20260417_103000.json
```

### 5.2 文件命名规则

| 层级 | 规则 | 示例 |
|------|------|------|
| 一级目录 | 按 Agent 角色 | `design/`, `art/`, `code/`, `review/`, `meta/` |
| 二级目录 | 按文档类型 | `spec/`, `art_requirements/`, `manifest/`, `questions/` |
| 三级目录（仅 assets） | 按资源分类 | `character/`, `background/`, `item/`, `effect/`, `ui/` |
| 文件名 | `{类型}_{YYYYMMDD_HHMMSS}.{ext}` | `design_spec_20260417_103000.md` |

### 5.3 `latest.json` 索引文件

由 Python 编排器在每个阶段执行后更新，Agent 本身不操作此文件。

```json
{
  "run_id": "20260417_103000",
  "design": {
    "spec": "pipeline/outputs/design/spec/design_spec_20260417_103000.md",
    "art_requirements": "pipeline/outputs/design/art_requirements/art_requirements_20260417_103000.json",
    "art_answers": null
  },
  "art": {
    "questions": null,
    "manifest": "pipeline/outputs/art/manifest/art_manifest_20260417_110000.json",
    "assets": {
      "character": "pipeline/outputs/art/assets/character/",
      "background": "pipeline/outputs/art/assets/background/",
      "item": "pipeline/outputs/art/assets/item/",
      "effect": "pipeline/outputs/art/assets/effect/",
      "ui": "pipeline/outputs/art/assets/ui/"
    }
  },
  "code": {
    "questions": null,
    "project_dir": "BabySleep/"
  },
  "review": {
    "feedback": null
  }
}
```

### 5.4 每个 Agent 的输入文档清单

| Agent | 接收文档 | 说明 |
|-------|---------|------|
| Design Agent | 用户输入的游戏概念（字符串） | 首次执行，无历史文档 |
| Design Clarify | `design/spec/*` + `art/questions/*` | 读自己之前的设计 + 美术提问 |
| Art Preflight | `design/art_requirements/*` | 只需要美术需求清单 |
| Art Execute | `design/art_requirements/*` + `design/art_answers/*`（如有） | 需求 + 澄清答案 |
| Code Preflight | `art/manifest/*` | 只需要资产清单 |
| Art Fix | `art/manifest/*` + `code/questions/*` | 原始输出 + 问题列表 |
| Code Execute | `design/spec/*` + 最终 `art/manifest/*` | 设计文档 + 最终资产清单 |
| Reviewer | `design/spec/*` + 最终 `art/manifest/*` + `BabySleep/` 项目代码 | 全量输入 |

---

## 六、LangGraph 状态机

### 6.1 State 定义

```python
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
```

### 6.2 节点清单

共 9 个节点：

| 节点名 | 模型 | 职责 |
|--------|------|------|
| `design` | claude-opus-4-6 | 生成设计文档 + 美术需求 |
| `art_preflight` | qwen3.6-plus | 预检美术需求，判断是否有疑问 |
| `design_clarify` | claude-opus-4-6 | 回答美术提问 |
| `art_execute` | qwen3.6-plus | 执行生图 |
| `code_preflight` | 无（纯 Python） | 预检资源完整性（检查文件存在、格式、尺寸） |
| `art_fix` | qwen3.6-plus | 修复资源问题 |
| `code_execute` | claude-opus-4-6 | 编写 Cocos 项目代码 |
| `review` | claude-opus-4-6 | 审查全部产出 |
| `finalize` | 无（纯 Python） | 生成最终运行报告并写入 `meta/run_log/` |

### 6.3 边与路由

**固定边：**

```
design → art_preflight
design_clarify → art_execute        # 澄清后直接执行，不再预检
art_execute → code_preflight
art_fix → code_execute              # 修复后直接执行，不再预检
finalize → END
```

**条件边：**

```
art_preflight:
  has_questions → design_clarify
  no_questions  → art_execute

code_preflight:
  has_issues → art_fix
  no_issues  → code_execute

review:
  pass         → finalize
  retry_design → design          (retry_count < max_retries)
  retry_art    → art_execute     (retry_count < max_retries)
  retry_code   → code_execute    (retry_count < max_retries)
  max_retries  → finalize        (retry_count >= max_retries)
```

### 6.4 LangGraph 构建代码

```python
from langgraph.graph import StateGraph, END

def build_pipeline() -> StateGraph:
    graph = StateGraph(PipelineState)

    # 添加节点
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
    graph.add_edge("design_clarify", "art_execute")
    graph.add_edge("art_execute", "code_preflight")
    graph.add_edge("art_fix", "code_execute")
    graph.add_edge("finalize", END)

    # 条件边
    graph.add_conditional_edges("art_preflight", route_art_preflight,
        {"has_questions": "design_clarify", "no_questions": "art_execute"})

    graph.add_conditional_edges("code_preflight", route_code_preflight,
        {"has_issues": "art_fix", "no_issues": "code_execute"})

    graph.add_conditional_edges("review", route_review,
        {"pass": "finalize", "retry_design": "design",
         "retry_art": "art_execute", "retry_code": "code_execute",
         "max_retries": "finalize"})

    return graph.compile()
```

### 6.5 路由函数

```python
def route_art_preflight(state: PipelineState) -> str:
    if state["art_preflight_pass"]:
        return "no_questions"
    return "has_questions"

def route_code_preflight(state: PipelineState) -> str:
    if state["code_preflight_pass"]:
        return "no_issues"
    return "has_issues"

def route_review(state: PipelineState) -> str:
    if state["review_verdict"] == "pass":
        return "pass"
    if state["retry_count"] >= state["max_retries"]:
        return "max_retries"
    target = state["review_target"]
    return f"retry_{target}"
```

### 6.6 节点执行模板

每个节点统一执行三步：**准备 prompt → 调用 CodeMaker → 更新 state**

```python
import subprocess, json, os
from datetime import datetime

def design_node(state: PipelineState) -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    root = state["project_root"]

    # 1. 确定输出路径
    spec_path = f"pipeline/outputs/design/spec/design_spec_{ts}.md"
    art_req_path = f"pipeline/outputs/design/art_requirements/art_requirements_{ts}.json"

    # 2. 确保目录存在
    os.makedirs(os.path.join(root, "pipeline/outputs/design/spec"), exist_ok=True)
    os.makedirs(os.path.join(root, "pipeline/outputs/design/art_requirements"), exist_ok=True)

    # 3. 拼装 prompt
    prompt = f"""你是一位资深游戏策划。请根据以下游戏概念，生成完整的设计文档和美术需求清单。

游戏概念：{state["game_concept"]}

请将设计文档写入：{spec_path}
请将美术需求清单写入：{art_req_path}
美术需求清单格式请严格遵守 JSON schema（见 prompt 末尾）。
..."""

    # 4. 调用 CodeMaker
    result = subprocess.run(
        ["codemaker", "run", "-m", "netease-codemaker/claude-opus-4-6", prompt],
        cwd=root, capture_output=True, text=True, timeout=600
    )

    # 5. 更新 latest 索引
    latest = state["latest"]
    latest["design"]["spec"] = spec_path
    latest["design"]["art_requirements"] = art_req_path

    # 6. 写入 latest.json
    with open(os.path.join(root, "pipeline/outputs/latest.json"), "w") as f:
        json.dump(latest, f, indent=2, ensure_ascii=False)

    return {
        "current_phase": "design_done",
        "latest": latest
    }
```

### 6.7 运行入口

```python
from datetime import datetime

def run_pipeline(game_concept: str, project_root: str, max_retries: int = 3):
    pipeline = build_pipeline()

    initial_state: PipelineState = {
        "game_concept": game_concept,
        "project_root": project_root,
        "run_id": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "current_phase": "init",
        "retry_count": 0,
        "max_retries": max_retries,
        "latest": {
            "design": {"spec": None, "art_requirements": None, "art_answers": None},
            "art": {"questions": None, "manifest": None, "assets": {}},
            "code": {"questions": None, "project_dir": "BabySleep/"},
            "review": {"feedback": None}
        },
        "art_preflight_pass": True,
        "code_preflight_pass": True,
        "review_verdict": None,
        "review_target": None,
        "status": "running",
        "final_message": ""
    }

    final_state = pipeline.invoke(initial_state)
    print(f"Pipeline 完成: {final_state['status']}")
    print(final_state["final_message"])
```

---

## 七、项目文件结构

```
pipeline/
├── main.py                        # 运行入口
├── state.py                       # PipelineState 定义
├── graph.py                       # LangGraph 构建（build_pipeline）
├── agent.py                       # invoke_agent 通用调用函数
├── nodes/
│   ├── design.py                  # design_node
│   ├── art_preflight.py           # art_preflight_node
│   ├── design_clarify.py          # design_clarify_node
│   ├── art_execute.py             # art_execute_node
│   ├── code_preflight.py          # code_preflight_node
│   ├── art_fix.py                 # art_fix_node
│   ├── code_execute.py            # code_execute_node
│   ├── review.py                  # review_node
│   └── finalize.py                # finalize_node
├── prompts/
│   ├── design_system.md           # 策划 Agent 系统指令
│   ├── art_system.md              # 美术 Agent 系统指令
│   ├── code_system.md             # 代码 Agent 系统指令
│   └── reviewer_system.md         # Reviewer 系统指令
├── outputs/                       # 运行时产物（.gitignore）
│   └── latest.json
├── requirements.txt               # langgraph 等依赖
└── README.md                      # 使用说明
```

---

## 八、依赖清单

```
langgraph>=0.2.0
requests             # free_image_generator.py 已使用
```

无需额外 LLM SDK，所有模型调用通过 `codemaker run` CLI。

---

## 九、finalize 节点与运行日志

### 9.1 finalize 节点

`finalize` 是纯 Python 节点，不调用 LLM。职责：

1. 汇总本次运行的所有阶段执行结果
2. 生成运行日志写入 `meta/run_log/`
3. 在终端打印最终报告

### 9.2 `run_log.json` 格式

```json
{
  "run_id": "20260417_103000",
  "status": "passed",
  "started_at": "2026-04-17T10:30:00",
  "finished_at": "2026-04-17T11:45:00",
  "duration_seconds": 4500,
  "retry_count": 1,
  "phases": [
    {
      "name": "design",
      "status": "success",
      "started_at": "2026-04-17T10:30:00",
      "finished_at": "2026-04-17T10:35:00",
      "outputs": ["design/spec/design_spec_20260417_103000.md", "design/art_requirements/art_requirements_20260417_103000.json"]
    },
    {
      "name": "art_preflight",
      "status": "pass",
      "note": "无疑问，直接通过"
    }
  ],
  "final_outputs": {
    "design_spec": "pipeline/outputs/design/spec/design_spec_20260417_103000.md",
    "art_manifest": "pipeline/outputs/art/manifest/art_manifest_20260417_110000.json",
    "project_dir": "BabySleep/"
  }
}
```

---

## 十、code_preflight 纯 Python 实现说明

`code_preflight` 不需要 LLM，用纯 Python 检查即可，更快更可靠：

```python
def code_preflight_node(state: PipelineState) -> dict:
    """纯 Python 预检：检查美术资源完整性"""
    root = state["project_root"]
    manifest_path = os.path.join(root, state["latest"]["art"]["manifest"])

    with open(manifest_path, "r") as f:
        manifest = json.load(f)

    issues = []
    for asset in manifest["assets"]:
        file_path = os.path.join(root, asset["file_path"])
        # 检查文件是否存在
        if not os.path.exists(file_path):
            issues.append({"id": asset["id"], "issue": "文件不存在", "path": asset["file_path"]})
            continue
        # 检查文件大小（空文件视为失败）
        if os.path.getsize(file_path) == 0:
            issues.append({"id": asset["id"], "issue": "文件为空", "path": asset["file_path"]})
        # 检查生成状态
        if asset.get("status") != "success":
            issues.append({"id": asset["id"], "issue": f"生成状态异常: {asset.get('status')}", "path": asset["file_path"]})

    if issues:
        # 写入提问文件
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        questions_path = f"pipeline/outputs/code/questions/code_questions_{ts}.json"
        os.makedirs(os.path.join(root, "pipeline/outputs/code/questions"), exist_ok=True)
        with open(os.path.join(root, questions_path), "w") as f:
            json.dump({"issues": issues, "request": "请重新生成以下失败的资源"}, f, indent=2, ensure_ascii=False)
        latest = state["latest"]
        latest["code"]["questions"] = questions_path
        return {"code_preflight_pass": False, "latest": latest}

    return {"code_preflight_pass": True}
```

---

## 十一、错误处理策略

| 错误类型 | 处理方式 |
|---------|---------|
| CodeMaker CLI 非零退出码 | 原地重试 1 次，再失败则 pipeline 终止 |
| CodeMaker CLI 超时 | 同上 |
| Agent 输出文件不存在/格式错误 | 记录到 run_log，pipeline 终止 |
| Pollinations API 单张图片失败 | 美术 Agent 应跳过该图，在 manifest 中标记 `status: "failed"`，由 code_preflight 捕获 |
| Reviewer 返回无法解析的 JSON | 视为 `fail`，target 默认为 `"code"` |
| 达到最大重试次数 | pipeline 终止，finalize 输出包含未解决问题的报告 |
