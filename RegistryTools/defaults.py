"""
默认工具集配置

提供预定义的工具元数据和冷热分离配置。

Copyright (c) 2026 Maric
License: MIT
"""

from pathlib import Path

from RegistryTools.registry.models import ToolMetadata

# ============================================================
# 冷热工具分类配置 (TASK-802)
# ============================================================

# 冷热工具分类阈值
HOT_TOOL_THRESHOLD = 10
"""热工具: 使用频率 ≥ 10"""

WARM_TOOL_THRESHOLD = 3
"""温工具: 使用频率 ≥ 3"""

# 降级机制配置
HOT_TOOL_INACTIVE_DAYS = 30
"""热工具 30 天未使用降级为温工具"""

WARM_TOOL_INACTIVE_DAYS = 60
"""温工具 60 天未使用降级为冷工具"""

# 预加载配置
MAX_HOT_TOOLS_PRELOAD = 100
"""最多预加载的热工具数量"""

ENABLE_DOWNGRADE = True
"""是否启用工具降级机制"""

# ============================================================
# 默认工具集 (TASK-603)
# ============================================================


def get_default_tools() -> list[ToolMetadata]:
    """
    获取默认工具集

    返回预定义的工具元数据列表，用于首次启动时的初始化。
    这些工具主要来自常见的 MCP 服务器。

    Returns:
        默认工具元数据列表
    """
    return [
        # ========================================================
        # GitHub 工具
        # ========================================================
        ToolMetadata(
            name="github.add_issue_comment",
            description="Add a comment to a specific issue in a GitHub repository",
            mcp_server="github",
            tags={"github", "issues", "comments"},
            category="github",
        ),
        ToolMetadata(
            name="github.create_branch",
            description="Create a new branch in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "branches"},
            category="github",
        ),
        ToolMetadata(
            name="github.create_issue",
            description="Create a new issue in a GitHub repository",
            mcp_server="github",
            tags={"github", "issues"},
            category="github",
        ),
        ToolMetadata(
            name="github.create_or_update_file",
            description="Create or update a single file in a GitHub repository",
            mcp_server="github",
            tags={"github", "files", "repository"},
            category="github",
        ),
        ToolMetadata(
            name="github.create_pull_request",
            description="Create a new pull request in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="github.get_file_contents",
            description="Get the contents of a file or directory from a GitHub repository",
            mcp_server="github",
            tags={"github", "files", "repository"},
            category="github",
        ),
        ToolMetadata(
            name="github.list_pull_requests",
            description="List pull requests in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr"},
            category="github",
        ),
        ToolMetadata(
            name="github.merge_pull_request",
            description="Merge a pull request in a GitHub repository",
            mcp_server="github",
            tags={"github", "git", "pr", "merge"},
            category="github",
        ),
        # ========================================================
        # AWS 工具
        # ========================================================
        ToolMetadata(
            name="aws.s3.upload",
            description="Upload file to S3 bucket",
            mcp_server="aws",
            tags={"aws", "s3", "storage", "upload"},
            category="aws",
        ),
        ToolMetadata(
            name="aws.s3.download",
            description="Download file from S3 bucket",
            mcp_server="aws",
            tags={"aws", "s3", "storage", "download"},
            category="aws",
        ),
        ToolMetadata(
            name="aws.lambda.invoke",
            description="Invoke AWS Lambda function",
            mcp_server="aws",
            tags={"aws", "lambda", "serverless"},
            category="aws",
        ),
        ToolMetadata(
            name="aws.ec2.describe_instances",
            description="Describe EC2 instances",
            mcp_server="aws",
            tags={"aws", "ec2", "compute"},
            category="aws",
        ),
        # ========================================================
        # Slack 工具
        # ========================================================
        ToolMetadata(
            name="slack.send_message",
            description="Send message to Slack channel",
            mcp_server="slack",
            tags={"slack", "messaging"},
            category="slack",
        ),
        ToolMetadata(
            name="slack.list_channels",
            description="List all Slack channels",
            mcp_server="slack",
            tags={"slack", "channels"},
            category="slack",
        ),
        ToolMetadata(
            name="slack.get_user_info",
            description="Get information about a Slack user",
            mcp_server="slack",
            tags={"slack", "users"},
            category="slack",
        ),
        # ========================================================
        # Google Drive 工具
        # ========================================================
        ToolMetadata(
            name="gdrive.list_files",
            description="List files in Google Drive",
            mcp_server="gdrive",
            tags={"google", "drive", "files"},
            category="google",
        ),
        ToolMetadata(
            name="gdrive.upload_file",
            description="Upload file to Google Drive",
            mcp_server="gdrive",
            tags={"google", "drive", "upload"},
            category="google",
        ),
        ToolMetadata(
            name="gdrive.search_files",
            description="Search files in Google Drive",
            mcp_server="gdrive",
            tags={"google", "drive", "search"},
            category="google",
        ),
        # ========================================================
        # 时间工具
        # ========================================================
        ToolMetadata(
            name="time.convert_timezone",
            description="Convert time between timezones, get current time in any location",
            mcp_server="time-timezone-converter",
            tags={"time", "timezone", "converter"},
            category="utilities",
        ),
        # ========================================================
        # 数据库工具
        # ========================================================
        ToolMetadata(
            name="database.query",
            description="Execute SQL query on database",
            mcp_server="postgres",
            tags={"database", "sql", "query"},
            category="database",
        ),
        ToolMetadata(
            name="database.list_tables",
            description="List all tables in database",
            mcp_server="postgres",
            tags={"database", "sql", "tables"},
            category="database",
        ),
        # ========================================================
        # 文件系统工具
        # ========================================================
        ToolMetadata(
            name="filesystem.read_file",
            description="Read contents of a file",
            mcp_server="filesystem",
            tags={"filesystem", "files", "read"},
            category="filesystem",
        ),
        ToolMetadata(
            name="filesystem.write_file",
            description="Write content to a file",
            mcp_server="filesystem",
            tags={"filesystem", "files", "write"},
            category="filesystem",
        ),
        ToolMetadata(
            name="filesystem.list_directory",
            description="List contents of a directory",
            mcp_server="filesystem",
            tags={"filesystem", "directory", "list"},
            category="filesystem",
        ),
    ]


def load_default_tools_if_empty(
    tool_count: int,
    storage_path: Path | None = None,
    auto_save: bool = True,
) -> list[ToolMetadata]:
    """
    如果注册表为空，加载默认工具集

    Args:
        tool_count: 当前工具数量
        storage_path: 存储路径（可选）
        auto_save: 是否自动保存到存储

    Returns:
        默认工具列表（如果已加载），否则返回空列表
    """
    # 如果已有工具，不加载默认集
    if tool_count > 0:
        return []

    # 获取默认工具
    default_tools = get_default_tools()

    # 如果需要自动保存且提供了存储路径
    if auto_save and storage_path:
        from RegistryTools.storage.json_storage import JSONStorage

        storage = JSONStorage(storage_path)
        storage.initialize()
        storage.save_many(default_tools)

    return default_tools
