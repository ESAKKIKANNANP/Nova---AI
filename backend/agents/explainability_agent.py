# =============================================================================
# backend/agents/explainability_agent.py
#
# The LangChain agent that translates SHAP values into business insights.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.explainability_prompts import get_explainability_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class ExplainabilitySummary(BaseModel):
    executive_summary: str = Field(..., description="A high-level business summary.")
    business_insights: List[str] = Field(..., description="Actionable insights derived from the model.")
    markdown_report: str = Field(..., description="A formatted markdown string ready to be converted to PDF.")

class ExplainabilityAgent:
    """
    Translates raw SHAP feature importances into executive business reports.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.prompt = get_explainability_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(ExplainabilitySummary)

    async def ainvoke(self, state: GraphState, feature_importance: Dict[str, float], config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Explainability Agent...")
        
        problem_type = state.get("data_profile", {}).get("problem_type", "Unknown")
        
        # We only pass the top 10 features to the LLM to avoid token limits
        top_10_features = dict(list(feature_importance.items())[:10])
        
        plan: ExplainabilitySummary = await self.chain.ainvoke({
            "problem_type": problem_type,
            "feature_importance": str(top_10_features)
        }, config=config)
        
        return {
            "agent_name": "explainability_agent",
            "output": plan.model_dump(),
            "validated": True
        }
