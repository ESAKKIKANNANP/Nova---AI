# =============================================================================
# backend/api/schemas/analysis.py
#
# Pydantic schemas for the Analysis endpoints.
# =============================================================================

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import uuid

class AnalyzeRequest(BaseModel):
    """Request payload to trigger an analysis."""
    dataset_id: str = Field(..., description="ID of the dataset to analyze")
    project_id: str = Field(..., description="Project ID (used as thread_id for isolation)")
    user_goal: str = Field(..., description="Natural language goal of the analysis")

class AnalyzeResponse(BaseModel):
    """Response returned immediately when analysis is queued."""
    job_id: str = Field(..., description="The ID of the background job (maps to project_id)")
    status: str = Field(default="queued", description="Status of the job")
    message: str = Field(default="Analysis job has been started in the background.")

class StatusResponse(BaseModel):
    """Current state of the LangGraph execution."""
    job_id: str
    current_node: Optional[str] = Field(None, description="The node currently executing or last executed")
    is_complete: bool = Field(False, description="True if the pipeline reached the END node successfully")
    error_message: Optional[str] = Field(None, description="Present if the graph execution failed")
    execution_results: Dict[str, Any] = Field(default_factory=dict, description="Metadata and results from executed nodes")

class ReportResponse(BaseModel):
    """The final markdown report and artifacts."""
    job_id: str
    markdown_report: Optional[str] = Field(None, description="The final generated report text")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Links to generated charts and models")
