# =============================================================================
# backend/agents/business_insight_agent.py
#
# The LangChain agent that generates the final C-level executive JSON.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.insight_prompts import get_insight_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class BusinessInsightReport(BaseModel):
    executive_summary: str = Field(..., description="One paragraph high-level overview.")
    business_insights: List[str] = Field(..., description="Top 3-5 analytical findings derived from EDA and SHAP.")
    recommendations: List[str] = Field(..., description="Strategic business actions based on the model.")
    risk_analysis: List[str] = Field(..., description="Potential pitfalls or model weaknesses based on evaluation metrics.")
    next_steps: List[str] = Field(..., description="Immediate next actions.")

class BusinessInsightAgent:
    """
    Synthesizes EDA, Evaluation, and Explainability into a master report.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.prompt = get_insight_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(BusinessInsightReport)

    async def ainvoke(
        self, 
        state: GraphState, 
        eda_summary: str, 
        eval_metrics: Dict[str, Any], 
        explain_summary: str, 
        config: RunnableConfig | None = None
    ) -> Dict[str, Any]:
        log.info("Invoking Business Insight Agent...")
        
        report: BusinessInsightReport = await self.chain.ainvoke({
            "eda_summary": eda_summary,
            "eval_metrics": str(eval_metrics),
            "explain_summary": explain_summary
        }, config=config)
        
        return {
            "agent_name": "business_insight_agent",
            "output": report.model_dump(),
            "validated": True
        }
