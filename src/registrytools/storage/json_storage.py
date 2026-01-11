"""
JSON 文件存储实现

使用 JSON 文件持久化工具元数据。

Copyright (c) 2026 Maric
License: MIT
"""

import json
import logging
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import TYPE_CHECKING

from pydantic import ValidationError

from registrytools.defaults import HOT_TOOL_THRESHOLD, WARM_TOOL_THRESHOLD
from registrytools.registry.models import ToolMetadata, ToolTemperature
from registrytools.storage.base import ToolStorage

# TYPE_CHECKING 块保留用于其他前向引用
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class JSONStorage(ToolStorage):
    """
    JSON 文件存储实现

    将工具元数据存储为 JSON 文件。数据格式为字典结构：
    ```json
    {
        "tool_name_1": { ...metadata... },
        "tool_name_2": { ...metadata... }
    }
    ```

    Attributes:
        _path: JSON 文件路径
    """

    def __init__(self, path: str | Path) -> None:
        """
        初始化 JSON 存储

        Args:
            path: JSON 文件路径（如 ~/.RegistryTools/tools.json）
        """
        super().__init__(path)
        # 确保是 .json 文件
        if self._path.suffix != ".json":
            self._path = self._path.with_suffix(".json")

    # ============================================================
    # 核心方法实现 (TASK-402)
    # ============================================================

    def load_all(self) -> list[ToolMetadata]:
        """
        加载所有工具元数据

        Returns:
            工具元数据列表

        Raises:
            FileNotFoundError: 如果 JSON 文件不存在
            IOError: 如果读取失败
        """
        if not self._path.exists():
            # 返回空列表而不是抛出异常
            return []

        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)

            # 将字典转换为 ToolMetadata 列表
            tools = []
            for tool_data in data.values():
                try:
                    tool = ToolMetadata(**tool_data)
                    tools.append(tool)
                except ValidationError as e:
                    # 跳过无效的工具数据，记录警告
                    tool_name = tool_data.get("name", "<unknown>")
                    logger.warning(f"跳过无效的工具数据: {tool_name}, 错误: {e}")
                    continue
                except Exception as e:
                    # 捕获其他意外错误
                    tool_name = tool_data.get("name", "<unknown>")
                    logger.error(f"加载工具数据时发生意外错误: {tool_name}, 错误: {e}")
                    continue

            return tools

        except json.JSONDecodeError as e:
            raise OSError(f"JSON 文件格式错误: {e}") from e

    def save(self, tool: ToolMetadata) -> None:
        """
        保存单个工具元数据

        如果工具已存在，则更新其元数据。

        Args:
            tool: 工具元数据

        Raises:
            IOError: 如果保存失败
        """
        # 加载现有数据
        if self._path.exists():
            try:
                with open(self._path, encoding="utf-8") as f:
                    data = json.load(f)
            except (OSError, json.JSONDecodeError):
                # 如果文件损坏，重新开始
                data = {}
        else:
            data = {}

        # 更新工具数据
        data[tool.name] = tool.model_dump(mode="json")

        # 原子写入
        self._write_atomic(data)

    def save_many(self, tools: list[ToolMetadata]) -> None:
        """
        批量保存工具元数据

        Args:
            tools: 工具元数据列表

        Raises:
            IOError: 如果保存失败
        """
        if not tools:
            return

        # 构建字典
        data = {tool.name: tool.model_dump(mode="json") for tool in tools}

        # 原子写入
        self._write_atomic(data)

    def delete(self, tool_name: str) -> bool:
        """
        删除工具元数据

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在并被删除，False 如果工具不存在

        Raises:
            IOError: 如果删除失败
        """
        if not self._path.exists():
            return False

        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)

            if tool_name not in data:
                return False

            # 删除工具
            del data[tool_name]

            # 如果没有工具了，删除文件
            if not data:
                self._path.unlink()
            else:
                # 否则原子写入
                self._write_atomic(data)

            return True

        except (OSError, json.JSONDecodeError) as e:
            raise OSError(f"删除工具失败: {e}") from e

    def exists(self, tool_name: str) -> bool:
        """
        检查工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在，否则 False
        """
        if not self._path.exists():
            return False

        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            return tool_name in data
        except (OSError, json.JSONDecodeError):
            return False

    def load_by_temperature(
        self,
        temperature: ToolTemperature,
        limit: int | None = None,
    ) -> list[ToolMetadata]:
        """
        按温度级别加载工具 (TASK-802)

        JSON 实现版本：加载全部工具后过滤。

        Args:
            temperature: 温度级别 (HOT/WARM/COLD)
            limit: 加载数量限制

        Returns:
            工具元数据列表
        """
        # 加载所有工具
        all_tools = self.load_all()

        # 根据温度过滤（使用枚举比较）
        if temperature == ToolTemperature.HOT:
            filtered = [t for t in all_tools if t.use_frequency >= HOT_TOOL_THRESHOLD]
        elif temperature == ToolTemperature.WARM:
            filtered = [
                t for t in all_tools if WARM_TOOL_THRESHOLD <= t.use_frequency < HOT_TOOL_THRESHOLD
            ]
        else:  # ToolTemperature.COLD
            filtered = [t for t in all_tools if t.use_frequency < WARM_TOOL_THRESHOLD]

        # 应用限制
        return filtered[:limit] if limit else filtered

    # ============================================================
    # 优化的工具方法
    # ============================================================

    def count(self) -> int:
        """
        获取工具数量

        Returns:
            工具数量
        """
        if not self._path.exists():
            return 0

        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)
            return len(data)
        except (OSError, json.JSONDecodeError):
            return 0

    def is_empty(self) -> bool:
        """
        检查存储是否为空

        Returns:
            True 如果存储为空，否则 False
        """
        return self.count() == 0

    def get(self, tool_name: str) -> ToolMetadata | None:
        """
        获取指定工具的元数据

        Args:
            tool_name: 工具名称

        Returns:
            工具元数据，如果不存在则返回 None
        """
        if not self._path.exists():
            return None

        try:
            with open(self._path, encoding="utf-8") as f:
                data = json.load(f)

            if tool_name not in data:
                return None

            return ToolMetadata(**data[tool_name])

        except (OSError, json.JSONDecodeError):
            return None

    def clear(self) -> None:
        """
        清空所有工具元数据

        删除 JSON 文件。
        """
        if self._path.exists():
            self._path.unlink()

    def initialize(self) -> None:
        """
        初始化存储

        创建父目录和空 JSON 文件。
        """
        super().initialize()
        # 如果文件不存在，创建空文件
        if not self._path.exists():
            self._write_atomic({})

    def validate(self) -> bool:
        """
        验证存储完整性

        Returns:
            True 如果存储有效，否则 False
        """
        try:
            if not self._path.exists():
                return False
            if not self._path.is_file():
                return False
            # 尝试解析 JSON
            with open(self._path, encoding="utf-8") as f:
                json.load(f)
            return True
        except Exception:
            return False

    # ============================================================
    # 私有辅助方法
    # ============================================================

    def _write_atomic(self, data: dict) -> None:
        """
        原子写入 JSON 数据

        使用临时文件 + 重命名的方式确保写入原子性。

        Args:
            data: 要写入的字典数据

        Raises:
            IOError: 如果写入失败
        """
        # 确保父目录存在
        self._path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # 创建临时文件
            with NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                suffix=".json",
                dir=self._path.parent,
                delete=False,
            ) as tmp_file:
                # 写入 JSON 数据（带缩进和排序，便于阅读）
                json.dump(data, tmp_file, ensure_ascii=False, indent=2, sort_keys=True)
                tmp_path = Path(tmp_file.name)

            # 原子重命名
            tmp_path.replace(self._path)

        except OSError as e:
            # 清理临时文件
            if "tmp_path" in locals() and tmp_path.exists():
                tmp_path.unlink()
            raise OSError(f"写入 JSON 文件失败: {e}") from e
