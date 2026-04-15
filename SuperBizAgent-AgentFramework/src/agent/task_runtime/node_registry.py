from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class NodeParamSpec:
    name: str
    type: str
    required: bool
    description: str
    default: Any = None


@dataclass
class TaskNodeSpec:
    node_id: str
    title: str
    stage: str
    description: str
    input_params: List[NodeParamSpec] = field(default_factory=list)
    output_fields: List[NodeParamSpec] = field(default_factory=list)
    supports_single_step: bool = True


def get_default_task_nodes() -> List[TaskNodeSpec]:
    return [
        TaskNodeSpec(
            node_id="multimodal_to_text",
            title="多模态转文本",
            stage="multimodal_ingest",
            description="将多模态输入（文件/文本）统一转换为 transcript 文本，供后续 AI 总结与文档生成复用。",
            input_params=[
                NodeParamSpec("input_mode", "string", True, "输入模态：multimodal_file | plain_text。"),
                NodeParamSpec("input_file", "string", False, "当 input_mode=multimodal_file 时的文件路径。"),
                NodeParamSpec("input_text", "string", False, "当 input_mode=plain_text 时的原始文本。"),
            ],
            output_fields=[
                NodeParamSpec("transcript", "string", True, "提取后的文本内容。"),
                NodeParamSpec("result_data", "object", True, "标准化结果数据，至少包含 transcript。"),
                NodeParamSpec("status", "string", True, "节点状态：success/failed/skipped。"),
            ],
        ),
        TaskNodeSpec(
            node_id="download_video",
            title="下载视频",
            stage="download",
            description="从链接下载视频文件到本地目录，供后续转写与分析使用。",
            input_params=[
                NodeParamSpec("link", "string", True, "待下载的视频链接。"),
                NodeParamSpec("timeout_sec", "int", False, "下载超时时间（秒）。", 120),
                NodeParamSpec("retry_count", "int", False, "下载失败时重试次数。", 2),
            ],
            output_fields=[
                NodeParamSpec("video_file", "string", True, "本地视频文件路径。"),
                NodeParamSpec("status", "string", True, "下载状态：success/failed。"),
                NodeParamSpec("error", "string", False, "失败时错误信息。"),
            ],
        ),
        TaskNodeSpec(
            node_id="speech_to_text",
            title="语音转文字",
            stage="transcribe",
            description="对已下载的视频进行语音转写，生成 transcript 与分段信息。",
            input_params=[
                NodeParamSpec("video_file", "string", True, "本地视频文件路径。"),
                NodeParamSpec("user_prompt", "string", False, "可选转写辅助提示。", ""),
            ],
            output_fields=[
                NodeParamSpec("transcript", "string", True, "完整转写文本。"),
                NodeParamSpec("segments", "array", False, "分段时间戳与文本。"),
                NodeParamSpec("status", "string", True, "转写状态：success/failed。"),
            ],
        ),
        TaskNodeSpec(
            node_id="summarize_content",
            title="AI 总结",
            stage="ai_analysis",
            description="调用模型对转写文本或图文内容进行总结与结构化提炼。",
            input_params=[
                NodeParamSpec("transcript", "string", True, "待总结文本。"),
                NodeParamSpec("user_prompt", "string", False, "自定义总结提示。", ""),
                NodeParamSpec("model_endpoint", "string", False, "可选指定模型接入点。", ""),
            ],
            output_fields=[
                NodeParamSpec("ai_summary", "string", True, "AI 总结结果。"),
                NodeParamSpec("title", "string", False, "从总结中抽取的标题。"),
                NodeParamSpec("status", "string", True, "总结状态：success/failed。"),
            ],
        ),
        TaskNodeSpec(
            node_id="generate_markdown",
            title="生成 Markdown",
            stage="generate_md",
            description="将转写与总结结果生成结构化 Markdown 文档。",
            input_params=[
                NodeParamSpec("result_data", "object", True, "转写与总结的合并数据。"),
                NodeParamSpec("link", "string", True, "原始链接。"),
                NodeParamSpec("platform", "string", True, "平台类型，如 小红书/视频/公众号。"),
            ],
            output_fields=[
                NodeParamSpec("md_file", "string", True, "生成的 Markdown 文件路径。"),
                NodeParamSpec("status", "string", True, "生成状态：success/failed。"),
            ],
        ),
        TaskNodeSpec(
            node_id="agent_process",
            title="Agent 处理节点",
            stage="agent",
            description="使用 Agent 进行中间处理，可配置 Prompt、入参来源与输出模板。",
            input_params=[
                NodeParamSpec("prompt", "string", True, "Agent 节点提示词（支持模板变量）。"),
                NodeParamSpec(
                    "input_source",
                    "string",
                    True,
                    "入参来源：previous_output_json | task_context_json | custom_json。",
                    "previous_output_json",
                ),
                NodeParamSpec("custom_input_json", "object", False, "当 input_source=custom_json 时使用。", {}),
                NodeParamSpec(
                    "output_template",
                    "string",
                    False,
                    "输出模板（可直接填写，或由模板导入/下一节点参数模板生成）。",
                    "",
                ),
            ],
            output_fields=[
                NodeParamSpec("agent_output_json", "object", True, "Agent 处理输出 JSON。"),
                NodeParamSpec("status", "string", True, "节点状态：success/failed。"),
                NodeParamSpec("error", "string", False, "失败时错误信息。"),
            ],
        ),
        TaskNodeSpec(
            node_id="sync_feishu_only",
            title="单独同步飞书",
            stage="feishu_upload",
            description="对已有 Markdown 结果执行飞书同步，支持独立节点配置与运行。",
            input_params=[
                NodeParamSpec("md_file", "string", True, "待同步的 Markdown 文件。"),
                NodeParamSpec("feishu_folder_path", "string", False, "飞书文件夹路径（可覆盖默认）。", ""),
                NodeParamSpec("force_sync", "bool", False, "是否强制执行同步。", False),
            ],
            output_fields=[
                NodeParamSpec("doc_token", "string", False, "飞书文档 token。"),
                NodeParamSpec("status", "string", True, "同步状态：success/failed/skipped。"),
                NodeParamSpec("error", "string", False, "失败时错误信息。"),
            ],
        ),
    ]


def build_task_node_docs_markdown(nodes: List[TaskNodeSpec]) -> str:
    lines: List[str] = []
    lines.append("# 本地任务节点文档")
    lines.append("")
    lines.append("说明：以下节点为本地任务编排默认节点。每个节点均可单独配置输入参数。")
    lines.append("")
    for node in nodes:
        lines.append(f"## {node.title} (`{node.node_id}`)")
        lines.append(f"- 阶段: `{node.stage}`")
        lines.append(f"- 描述: {node.description}")
        lines.append("- 输入参数:")
        for p in node.input_params:
            req = "必填" if p.required else "可选"
            lines.append(
                f"  - `{p.name}` ({p.type}, {req})：{p.description}"
                + (f" 默认 `{p.default}`" if p.default not in (None, "") else "")
            )
        lines.append("- 输出字段:")
        for p in node.output_fields:
            req = "必有" if p.required else "可空"
            lines.append(f"  - `{p.name}` ({p.type}, {req})：{p.description}")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def nodes_to_dict(nodes: List[TaskNodeSpec]) -> Dict[str, Dict[str, Any]]:
    data: Dict[str, Dict[str, Any]] = {}
    for n in nodes:
        data[n.node_id] = {
            "title": n.title,
            "stage": n.stage,
            "description": n.description,
            "supports_single_step": n.supports_single_step,
            "input_params": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "description": p.description,
                    "default": p.default,
                }
                for p in n.input_params
            ],
            "output_fields": [
                {
                    "name": p.name,
                    "type": p.type,
                    "required": p.required,
                    "description": p.description,
                    "default": p.default,
                }
                for p in n.output_fields
            ],
        }
    return data

