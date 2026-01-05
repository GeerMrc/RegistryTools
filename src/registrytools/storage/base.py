"""
存储层抽象基类

定义所有存储实现的通用接口。

Copyright (c) 2026 Maric
License: MIT
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

from registrytools.registry.models import ToolMetadata

if TYPE_CHECKING:
    from registrytools.registry.models import ToolTemperature


class ToolStorage(ABC):
    """
    存储层抽象基类

    定义工具元数据持久化的通用接口。所有存储实现必须继承此类。

    Attributes:
        path: 存储路径（文件路径或目录路径）
    """

    def __init__(self, path: str | Path) -> None:
        """
        初始化存储层

        Args:
            path: 存储路径
        """
        self._path = Path(path)

    @property
    def path(self) -> Path:
        """获取存储路径"""
        return self._path

    # ============================================================
    # 核心抽象方法 (TASK-401)
    # ============================================================

    @abstractmethod
    def load_all(self) -> list[ToolMetadata]:
        """
        加载所有工具元数据

        Returns:
            工具元数据列表

        Raises:
            FileNotFoundError: 如果存储文件不存在
            IOError: 如果读取失败
        """
        pass

    @abstractmethod
    def save(self, tool: ToolMetadata) -> None:
        """
        保存单个工具元数据

        如果工具已存在，则更新其元数据。

        Args:
            tool: 工具元数据

        Raises:
            IOError: 如果保存失败
        """
        pass

    @abstractmethod
    def save_many(self, tools: list[ToolMetadata]) -> None:
        """
        批量保存工具元数据

        Args:
            tools: 工具元数据列表

        Raises:
            IOError: 如果保存失败
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    def exists(self, tool_name: str) -> bool:
        """
        检查工具是否存在

        Args:
            tool_name: 工具名称

        Returns:
            True 如果工具存在，否则 False
        """
        pass

    # ============================================================
    # 冷热分层加载接口 (TASK-802)
    # ============================================================

    @abstractmethod
    def load_by_temperature(
        self,
        temperature: "ToolTemperature",
        limit: int | None = None,
    ) -> list[ToolMetadata]:
        """
        按温度级别加载工具 (TASK-802)

        根据工具的使用频率（温度级别）加载工具。
        热工具：高频使用，预加载到内存
        温工具：中频使用，按需加载
        冷工具：低频使用，延迟加载

        Args:
            temperature: 温度级别 (HOT/WARM/COLD)
            limit: 加载数量限制，None 表示加载所有

        Returns:
            工具元数据列表

        Raises:
            FileNotFoundError: 如果存储文件不存在
            IOError: 如果读取失败
        """
        pass

    # ============================================================
    # 可选工具方法
    # ============================================================

    def clear(self) -> None:
        """
        清空所有工具元数据

        默认实现：逐个删除所有工具。子类可以覆盖以提供更高效的实现。

        Raises:
            IOError: 如果清空失败
        """
        tools = self.load_all()
        for tool in tools:
            self.delete(tool.name)

    def count(self) -> int:
        """
        获取工具数量

        默认实现：加载所有工具并计数。子类可以覆盖以提供更高效的实现。

        Returns:
            工具数量
        """
        return len(self.load_all())

    def is_empty(self) -> bool:
        """
        检查存储是否为空

        默认实现：检查工具数量是否为0。子类可以覆盖以提供更高效的实现。

        Returns:
            True 如果存储为空，否则 False
        """
        return self.count() == 0

    def get(self, tool_name: str) -> ToolMetadata | None:
        """
        获取指定工具的元数据

        默认实现：加载所有工具并查找。子类可以覆盖以提供更高效的实现。

        Args:
            tool_name: 工具名称

        Returns:
            工具元数据，如果不存在则返回 None
        """
        for tool in self.load_all():
            if tool.name == tool_name:
                return tool
        return None

    def initialize(self) -> None:
        """
        初始化存储

        创建必要的目录结构和初始文件。子类可以覆盖此方法以提供特定的初始化逻辑。
        """
        # 默认实现：确保父目录存在
        if self._path.suffix:  # 是文件路径
            self._path.parent.mkdir(parents=True, exist_ok=True)
        else:  # 是目录路径
            self._path.mkdir(parents=True, exist_ok=True)

    def validate(self) -> bool:
        """
        验证存储完整性

        检查存储是否存在且可访问。子类可以覆盖此方法以提供更详细的验证逻辑。

        Returns:
            True 如果存储有效，否则 False
        """
        try:
            # 检查路径是否存在
            if self._path.suffix:  # 是文件路径
                return self._path.exists() and self._path.is_file()
            else:  # 是目录路径
                return self._path.exists() and self._path.is_dir()
        except Exception:
            return False
