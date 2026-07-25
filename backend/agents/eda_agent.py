# =============================================================================
# agents/eda_agent.py
#
# Exploratory Data Analysis (EDA) Agent Implementation
#
# Architecture Decisions:
# 1. Two-Pass LLM Strategy: 
#    - Pass 1 (Planner): LLM decides *which* plots are statistically useful.
#    - Tool Execution: Python safely renders Plotly charts and computes summaries.
#    - Pass 2 (Reporter): LLM writes the Markdown report interpreting the tool summaries.
# 2. Plotly HTML Artifacts: Charts are saved as interactive HTML files. The LLM 
#    generates markdown links to them so they render in the frontend UI.
# 3. Structured Outputs: Both passes use `.with_structured_output` to prevent formatting errors.
# =============================================================================

import json
import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from graphs.state import GraphState, ArtifactDict
from prompts.eda_prompts import EDA_PLANNER_PROMPT, EDA_REPORTER_PROMPT
from tools.chart_renderer import generate_eda_plots

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output Schemas
# ---------------------------------------------------------------------------

class PlotRequest(BaseModel):
    """Schema for requesting a specific plot."""
    plot_type: str = Field(description="The type of plot (e.g., histogram, scatter_plot, correlation_matrix)")
    columns: List[str] = Field(description="The exact column names to use in the plot")
    reason: str = Field(description="Why this plot is useful for the analysis")

class EDAPlanOutput(BaseModel):
    """Output schema for Pass 1 (Planning)."""
    plots_to_generate: List[PlotRequest] = Field(description="List of requested plots")

class EDAReportOutput(BaseModel):
    """Output schema for Pass 2 (Reporting)."""
    markdown_report: str = Field(description="Comprehensive markdown report embedding the plots and explaining findings")
    key_findings: List[str] = Field(description="Bullet points of the most critical insights discovered")


# ---------------------------------------------------------------------------
# Agent Implementation
# ---------------------------------------------------------------------------

class EDAAgent:
    """
    The EDA Agent.
    Executes a two-pass pipeline: Plan Plots -> Render Plots -> Write Report.
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        
        # Planner Chain
        self.planner_llm = self.llm.with_structured_output(EDAPlanOutput)
        self.planner_prompt = ChatPromptTemplate.from_messages([
            ("system", EDA_PLANNER_PROMPT),
            ("user", "Determine the optimal plots to generate.")
        ])
        self.planner_chain = self.planner_prompt | self.planner_llm
        
        # Reporter Chain
        self.reporter_llm = self.llm.with_structured_output(EDAReportOutput)
        self.reporter_prompt = ChatPromptTemplate.from_messages([
            ("system", EDA_REPORTER_PROMPT),
            ("user", "Write the final EDA report.")
        ])
        self.reporter_chain = self.reporter_prompt | self.reporter_llm

    async def execute_eda(self, state: GraphState) -> Dict[str, Any]:
        """
        Executes the EDA node workflow.
        
        Args:
            state: The LangGraph state.
            
        Returns:
            Partial state update containing artifacts and execution results.
        """
        session_id = state.get("session_id", "unknown")
        dataset_path = state.get("dataset_path")
        user_goal = state.get("user_goal", "")
        data_profile = state.get("data_profile") or {}
        
        log.info(f"EDA Agent started for session {session_id}")
        
        if not dataset_path:
            raise ValueError("dataset_path is missing from the state. Cannot perform EDA.")
            
        try:
            # 1. Pass 1: Plan the plots
            profile_str = json.dumps(data_profile, indent=2)
            log.info("Requesting EDA plot plan from LLM...")
            
            plan: EDAPlanOutput = await self.planner_chain.ainvoke({
                "data_profile": profile_str,
                "user_goal": user_goal
            })
            
            log.info(f"LLM requested {len(plan.plots_to_generate)} plots.")
            
            # 2. Tool Execution: Render the plots using Python
            plot_requests = [p.dict() for p in plan.plots_to_generate]
            rendered_plots = generate_eda_plots(dataset_path, plot_requests)
            
            log.info(f"Successfully rendered {len(rendered_plots)} plots.")
            
            # Form artifacts list for the state
            artifacts: List[ArtifactDict] = []
            for plot in rendered_plots:
                artifacts.append({
                    "artifact_id": str(uuid.uuid4()),
                    "artifact_type": "chart",
                    "s3_path": plot["artifact_path"],
                    "mime_type": "text/html",
                    "title": f"{plot['plot_type']} of {', '.join(plot['columns'])}"
                })
                
            # 3. Pass 2: Generate the final Markdown report
            plot_summaries_str = json.dumps(rendered_plots, indent=2)
            log.info("Requesting EDA markdown report from LLM...")
            
            report: EDAReportOutput = await self.reporter_chain.ainvoke({
                "data_profile": profile_str,
                "plot_summaries": plot_summaries_str
            })
            
            log.info("EDA Agent completed successfully.")
            
            # Return partial state update
            return {
                "artifacts": artifacts,
                "execution_results": {
                    "eda_node": {
                        "report": report.markdown_report,
                        "key_findings": report.key_findings,
                        "generated_plots": len(artifacts)
                    }
                }
            }
            
        except Exception as exc:
            log.error(f"EDA Agent failed: {str(exc)}")
            raise RuntimeError(f"EDA Agent failed: {str(exc)}")
