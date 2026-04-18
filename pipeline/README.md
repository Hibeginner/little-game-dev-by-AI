# LangGraph 游戏开发流水线

多 Agent 协作的游戏自动开发流水线。通过 LangGraph 编排策划、美术、代码、审查四个 AI Agent，自动完成从游戏概念到可运行项目的全流程。

## 快速开始

```bash
# 进入 pipeline 目录（Python 包根目录）
cd pipeline

# 安装依赖
python3 -m pip install -r requirements.txt

# 运行（直接传入概念）
python3 main.py "一款休闲反应力游戏，玩家需要哄宝宝睡觉，处理各种随机干扰事件" --project-root D:\little-game

# 运行（从文件读取概念）
python3 main.py ../docs/superpowers/specs/2026-04-08-baby-sleep-design.md --project-root D:\little-game

# 指定重试次数 + 调试模式
python3 main.py "游戏概念" --project-root D:\little-game --max-retries 5 --log-level DEBUG
```

## 流水线阶段

```
Design Agent → Art Preflight → Art Execute → Code Preflight → Code Execute → Review
 (策划设计)     (美术预检)      (生成图片)     (资源预检)       (编写代码)     (审查)
```

1. **Design Agent** (claude-opus-4-6) — 生成设计文档 + 美术需求清单
2. **Art Preflight** (qwen3.6-plus) — 预检美术需求，必要时向策划提问（限 1 次）
3. **Art Execute** (qwen3.6-plus) — 使用 Pollinations.ai 免费 API 生成图片
4. **Code Preflight** (纯 Python) — 检查资源完整性（文件存在、格式、状态）
5. **Code Execute** (claude-opus-4-6) — 生成 Cocos Creator 3.x 项目代码
6. **Review** (claude-opus-4-6) — 自动审查，fail 时回退到对应 Agent（最多 3 次）

## 输出目录

运行产物保存在 `pipeline/outputs/` 下：

```
pipeline/outputs/
├── latest.json              # 最新文件索引
├── design/                  # 设计文档 + 美术需求
├── art/                     # 图片资源 + 资产清单
├── code/                    # 预检提问
├── review/                  # 审查反馈
└── meta/                    # 运行日志
```

## 技术栈

- **编排**: Python + LangGraph
- **Agent 运行时**: CodeMaker CLI (`codemaker run`)
- **图片生成**: Pollinations.ai (免费，无需 API Key)
- **最终产出**: Cocos Creator 3.x 项目
