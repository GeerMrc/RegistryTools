"""
数据模型定义

定义 RegistryTools 使用的所有数据模型。

Copyright (c) 2026 Maric
License: MIT
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field, field_serializer

# 避免循环导入：阈值常量仅在类型检查时使用
if TYPE_CHECKING:
    pass


class SearchMethod(str, Enum):
    """搜索方法枚举"""

    REGEX = "regex"
    """正则表达式精确匹配"""

    BM25 = "bm25"
    """BM25 关键词搜索"""

    EMBEDDING = "embedding"
    """语义向量搜索"""


class ToolTemperature(str, Enum):
    """工具温度级别枚举 (TASK-802)"""

    HOT = "hot"
    """热工具: 高频使用，预加载到内存"""

    WARM = "warm"
    """温工具: 中频使用，按需加载"""

    COLD = "cold"
    """冷工具: 低频使用，延迟加载"""


class ToolMetadata(BaseModel):
    """
    工具元数据模型

    存储工具的完整元数据信息，包括基本信息、分类、使用统计等。

    Attributes:
        name: 工具名称，唯一标识符
        description: 工具描述
        mcp_server: 所属 MCP 服务器名称（可选）
        defer_loading: 是否延迟加载，默认 True
        tags: 工具标签集合，用于分类和搜索
        category: 工具类别（可选）
        use_frequency: 使用频率统计
        last_used: 最后使用时间（可选）
        input_schema: 输入参数的 JSON Schema（可选）
        output_schema: 输出结果的 JSON Schema（可选）
    """

    name: str
    """工具名称，唯一标识符"""

    description: str
    """工具描述"""

    mcp_server: str | None = None
    """所属 MCP 服务器名称（可选）"""

    defer_loading: bool = True
    """是否延迟加载，默认 True"""

    tags: set[str] = Field(default_factory=set)
    """工具标签集合，用于分类和搜索"""

    category: str | None = None
    """工具类别（可选）"""

    use_frequency: int = 0
    """使用频率统计"""

    last_used: datetime | None = None
    """最后使用时间（可选）"""

    temperature: ToolTemperature = ToolTemperature.COLD
    """工具温度级别，默认为冷工具 (TASK-802)"""

    input_schema: dict | None = None
    """输入参数的 JSON Schema（可选）"""

    output_schema: dict | None = None
    """输出结果的 JSON Schema（可选）"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "github.create_pull_request",
                    "description": "Create a new pull request in a GitHub repository",
                    "mcp_server": "github",
                    "defer_loading": True,
                    "tags": ["github", "git", "pr"],
                    "category": "github",
                    "use_frequency": 0,
                    "last_used": None,
                }
            ]
        },
    )

    @field_serializer("tags")
    def serialize_tags(self, tags: set[str]) -> list[str]:
        """序列化 tags 字段为列表"""
        return list(tags)

    @field_serializer("last_used", when_used="json")
    def serialize_last_used(self, last_used: datetime | None) -> str | None:
        """序列化 last_used 字段为 ISO 格式字符串"""
        return last_used.isoformat() if last_used else None


class ToolSearchResult(BaseModel):
    """
    工具搜索结果模型

    存储工具搜索的结果信息。

    Attributes:
        tool_name: 工具名称
        description: 工具描述
        score: 相关度分数 (0-1)
        match_reason: 匹配原因（名称/描述/标签）
    """

    tool_name: str
    """工具名称"""

    description: str
    """工具描述"""

    score: float = Field(ge=0.0, le=1.0)
    """相关度分数 (0-1)"""

    match_reason: str
    """匹配原因（名称/描述/标签）"""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "tool_name": "github.create_pull_request",
                    "description": "Create a new pull request in a GitHub repository",
                    "score": 0.85,
                    "match_reason": "bm25_similarity",
                }
            ]
        }
    )
