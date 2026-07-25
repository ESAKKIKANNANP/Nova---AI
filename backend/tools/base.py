# =============================================================================
# backend/tools/base.py
#
# Base interfaces and return wrappers for the Autonomous Data Scientist tools.
# Every tool inherits from BaseTool to ensure identical argument schemas,
# validation checks, structured logger context, and clean outputs.
# =============================================================================

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type
import time
import structlog
from pydantic import BaseModel, ValidationError

logger = structlog.get_logger(__name__)


class ToolResult(BaseModel):
    """
    Standard envelope returned by all tools.
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    execution_time_ms: float
    metadata: Dict[str, Any] = {}


class BaseTool(ABC):
    """
    Abstract base class for all tools in the platform.
    """
    name: str
    description: str
    args_schema: Type[BaseModel]

    def __init__(self) -> None:
        if not hasattr(self, "name") or not self.name:
            raise ValueError(f"Tool {self.__class__.__name__} must define a name attribute.")
        if not hasattr(self, "description") or not self.description:
            raise ValueError(f"Tool {self.__class__.__name__} must define a description attribute.")
        if not hasattr(self, "args_schema") or not self.args_schema:
            raise ValueError(f"Tool {self.__class__.__name__} must define a Pydantic args_schema.")

    @abstractmethod
    def _run(self, **kwargs: Any) -> Any:
        """
        Core implementation logic of the tool. Must be overridden by subclasses.
        """
        pass

    def run(self, **kwargs: Any) -> ToolResult:
        """
        Public execution wrapper.
        Provides validation using the defined args_schema, executes core logic,
        handles exceptions, measures performance, and emits structured logs.
        """
        start_time = time.perf_counter()
        tool_logger = logger.bind(tool_name=self.name)

        # 1. Input Validation
        try:
            validated_args = self.args_schema(**kwargs)
        except ValidationError as val_err:
            tool_logger.warning("tool_validation_failed", error=str(val_err), inputs=kwargs)
            duration = (time.perf_counter() - start_time) * 1000
            return ToolResult(
                success=False,
                error=f"Argument validation failed: {val_err}",
                execution_time_ms=round(duration, 2),
                metadata={"inputs": kwargs}
            )

        # 2. Execution and Exception Handling
        try:
            tool_logger.info("tool_execution_started", inputs=validated_args.model_dump())
            result_data = self._run(**validated_args.model_dump())
            duration = (time.perf_counter() - start_time) * 1000
            tool_logger.info("tool_execution_success", duration_ms=round(duration, 2))
            
            return ToolResult(
                success=True,
                data=result_data,
                execution_time_ms=round(duration, 2)
            )
        except Exception as exc:
            duration = (time.perf_counter() - start_time) * 1000
            tool_logger.error("tool_execution_failed", error=str(exc), duration_ms=round(duration, 2))
            
            return ToolResult(
                success=False,
                error=str(exc),
                execution_time_ms=round(duration, 2)
            )
