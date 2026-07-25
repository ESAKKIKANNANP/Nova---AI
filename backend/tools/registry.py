# =============================================================================
# backend/tools/registry.py
#
# ToolRegistry: Central repository to register and retrieve execution tools.
# =============================================================================

from typing import Dict, List, Type
import structlog

from tools.base import BaseTool
from tools.code.code_executor import PythonExecutorTool
from tools.data.csv_loader import FileLoaderTool
from tools.data.sql_reader import SQLReaderTool
from tools.visualization.chart_renderer import ChartRendererTool
from tools.ml.model_trainer import ModelTrainerTool
from tools.external.rag_tool import RAGQueryTool

logger = structlog.get_logger(__name__)


class ToolRegistry:
    """
    Central registry keeping track of all operational tools available to agents.
    """
    def __init__(self) -> None:
        self._tools: Dict[str, BaseTool] = {}
        
        # Auto-register core platform tools
        self.register(PythonExecutorTool())
        self.register(FileLoaderTool())
        self.register(SQLReaderTool())
        self.register(ChartRendererTool())
        self.register(ModelTrainerTool())
        self.register(RAGQueryTool())

    def register(self, tool: BaseTool) -> None:
        """
        Registers a tool class instance in the registry.
        """
        if tool.name in self._tools:
            logger.warning("tool_overwritten", tool_name=tool.name)
        self._tools[tool.name] = tool
        logger.info("tool_registered", tool_name=tool.name)

    def get_tool(self, name: str) -> BaseTool:
        """
        Retrieves a registered tool by its unique name.
        """
        if name not in self._tools:
            raise KeyError(f"Tool '{name}' is not registered.")
        return self._tools[name]

    def list_tools(self) -> List[Dict[str, str]]:
        """
        Returns a list of dictionaries detailing all registered tools.
        """
        return [
            {
                "name": tool.name,
                "description": tool.description,
            }
            for tool in self._tools.values()
        ]


# Singleton instance for platform-wide usage
registry = ToolRegistry()
