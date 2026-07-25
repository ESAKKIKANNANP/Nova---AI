# =============================================================================
# backend/agents/report_generation_agent.py
#
# The LangChain agent that generates the final comprehensive JSON report structure.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.report_prompts import get_report_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class ReportData(BaseModel):
    executive_summary: str = Field(..., description="High-level overview of the entire project.")
    dataset_overview: str = Field(..., description="Summary of dataset shape, quality, and cleaning steps.")
    eda_summary: str = Field(..., description="Key findings from exploratory data analysis.")
    feature_engineering: str = Field(..., description="Summary of transformations applied to the data.")
    model_comparison: str = Field(..., description="Overview of the models trained and how they performed.")
    evaluation_metrics: str = Field(..., description="Detailed metrics of the winning model.")
    explainability: str = Field(..., description="Summary of what drives the model's predictions (SHAP/Feature Importance).")
    business_insights: List[str] = Field(..., description="Strategic insights.")
    recommendations: List[str] = Field(..., description="Actionable recommendations.")
    appendix: str = Field(..., description="Any technical details or closing remarks.")

class ReportGenerationAgent:
    """
    Synthesizes the entire pipeline into a structured master report.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.prompt = get_report_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(ReportData)

    async def ainvoke(
        self, 
        state: GraphState, 
        pipeline_context: str,
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        log.info("Invoking Report Generation Agent...")
        
        # We pass a massive stringified payload of all execution results
        report: ReportData = await self.chain.ainvoke({
            "pipeline_context": pipeline_context
        }, config=config)
        
        return {
            "agent_name": "report_generation_agent",
            "output": report.model_dump(),
            "validated": True
        }
