"""飞书固定落点发布：云空间文件夹 + 知识库节点，智能识别 URL，仅用 lark-cli。"""

from .feishu_target_url import ParsedTarget, parse_feishu_target

__all__ = ["ParsedTarget", "parse_feishu_target"]
