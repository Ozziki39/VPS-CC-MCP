"""
Base tool class and tool registry for VPS-CC-MCP.

All tools must:
1. Inherit from BaseTool
2. Define required metadata (name, approval_level, description, params_model)
3. Implement the execute() method
4. Register via the @register_tool decorator
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Optional, Type

from pydantic import BaseModel

from config import ApprovalLevel, get_approval_level
from context import ProjectContext
from schemas.requests import BaseToolParams
from schemas.responses import ToolResponse, ContextInfo
from session import Session


# Global tool registry
_tool_registry: dict[str, "BaseTool"] = {}


class ToolMetadata:
    """Metadata required for every tool."""

    def __init__(
        self,
        name: str,
        approval_level: ApprovalLevel,
        description: str,
        params_model: Type[BaseToolParams],
    ):
        self.name = name
        self.approval_level = approval_level
        self.description = description
        self.params_model = params_model

    def to_dict(self) -> dict[str, Any]:
        """Convert metadata to dictionary."""
        return {
            "name": self.name,
            "approval_level": self.approval_level.value,
            "description": self.description,
            "params_schema": self.params_model.model_json_schema(),
        }


class BaseTool(ABC):
    """
    Base class for all VPS-CC-MCP tools.

    Subclasses must define:
    - metadata: ToolMetadata with name, approval_level, description, params_model
    - execute(): The actual tool implementation
    """

    metadata: ToolMetadata

    def __init__(self, session: Session, context: ProjectContext):
        self.session = session
        self.context = context

    @classmethod
    def validate_metadata(cls) -> None:
        """Validate that required metadata is defined. Called at startup."""
        if not hasattr(cls, "metadata"):
            raise ValueError(f"Tool {cls.__name__} missing 'metadata' attribute")

        meta = cls.metadata
        if not isinstance(meta, ToolMetadata):
            raise ValueError(f"Tool {cls.__name__} 'metadata' must be ToolMetadata instance")

        if not meta.name:
            raise ValueError(f"Tool {cls.__name__} missing 'name' in metadata")
        if not meta.approval_level:
            raise ValueError(f"Tool {cls.__name__} missing 'approval_level' in metadata")
        if not meta.description:
            raise ValueError(f"Tool {cls.__name__} missing 'description' in metadata")
        if not meta.params_model:
            raise ValueError(f"Tool {cls.__name__} missing 'params_model' in metadata")

    def validate_params(self, params: dict[str, Any]) -> BaseToolParams:
        """Validate and parse parameters using the tool's params model."""
        return self.metadata.params_model.model_validate(params)

    @abstractmethod
    def execute(self, params: BaseToolParams) -> Any:
        """
        Execute the tool with validated parameters.

        Args:
            params: Validated parameters (instance of params_model).

        Returns:
            Tool-specific result data.

        Raises:
            Any exception will be caught and returned as error response.
        """
        pass

    def run(self, raw_params: dict[str, Any], auto_approve: bool = False) -> ToolResponse:
        """
        Run the tool with full error handling and response formatting.

        Args:
            raw_params: Raw parameter dictionary from CLI.
            auto_approve: Override approval checks.

        Returns:
            Structured ToolResponse.
        """
        context_info = ContextInfo(
            project=self.context.focus_path_str,
            session_id=self.session.session_id,
        )

        try:
            # Validate parameters
            params = self.validate_params(raw_params)

            # Check approval level
            if not auto_approve and self.metadata.approval_level == ApprovalLevel.EXPLICIT:
                return ToolResponse.error_response(
                    session_id=self.session.session_id,
                    tool=self.metadata.name,
                    approval_level=self.metadata.approval_level.value,
                    error_type="ApprovalRequired",
                    error_message=(
                        f"Tool '{self.metadata.name}' requires explicit approval. "
                        "Use --auto-approve flag to execute."
                    ),
                    context=context_info,
                )

            # Handle dry run
            if params.dry_run:
                return ToolResponse.success_response(
                    session_id=self.session.session_id,
                    tool=self.metadata.name,
                    approval_level=self.metadata.approval_level.value,
                    result={
                        "dry_run": True,
                        "would_execute": self.metadata.name,
                        "params": raw_params,
                        "approval_level": self.metadata.approval_level.value,
                    },
                    context=context_info,
                    dry_run=True,
                )

            # Execute the tool
            result = self.execute(params)

            # Log to session
            self.session.log_tool_call(
                tool=self.metadata.name,
                params=raw_params,
                result=result if isinstance(result, (dict, list, str, int, float, bool, type(None))) else str(result),
            )

            return ToolResponse.success_response(
                session_id=self.session.session_id,
                tool=self.metadata.name,
                approval_level=self.metadata.approval_level.value,
                result=result,
                context=context_info,
            )

        except Exception as e:
            # Log error to session
            error_info = {
                "type": type(e).__name__,
                "message": str(e),
            }
            self.session.log_tool_call(
                tool=self.metadata.name,
                params=raw_params,
                error=error_info,
            )

            return ToolResponse.error_response(
                session_id=self.session.session_id,
                tool=self.metadata.name,
                approval_level=self.metadata.approval_level.value,
                error_type=type(e).__name__,
                error_message=str(e),
                context=context_info,
            )


def register_tool(tool_class: Type[BaseTool]) -> Type[BaseTool]:
    """
    Decorator to register a tool in the global registry.

    Usage:
        @register_tool
        class MyTool(BaseTool):
            ...
    """
    # Validate metadata at registration time (fail fast)
    tool_class.validate_metadata()

    name = tool_class.metadata.name
    if name in _tool_registry:
        raise ValueError(f"Tool '{name}' is already registered")

    _tool_registry[name] = tool_class
    return tool_class


def get_tool(name: str) -> Optional[Type[BaseTool]]:
    """Get a tool class by name."""
    return _tool_registry.get(name)


def get_all_tools() -> dict[str, Type[BaseTool]]:
    """Get all registered tools."""
    return _tool_registry.copy()


def list_tools() -> list[dict[str, Any]]:
    """List all tools with their metadata."""
    return [
        tool_class.metadata.to_dict()
        for tool_class in _tool_registry.values()
    ]


def create_tool(
    name: str,
    session: Session,
    context: ProjectContext,
) -> Optional[BaseTool]:
    """Create a tool instance by name."""
    tool_class = get_tool(name)
    if tool_class is None:
        return None
    return tool_class(session, context)
