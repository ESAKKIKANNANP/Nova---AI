# =============================================================================
# backend/agents/evaluation_agent.py
#
# The LangChain agent that generates the final Model Evaluation report.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.evaluation_prompts import get_evaluation_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class EvaluationSummary(BaseModel):
    leaderboard: List[str] = Field(..., description="Ordered list of model names from best to worst.")
    markdown_report: str = Field(..., description="A professional markdown summary including the comparison table and strengths/weaknesses.")

class EvaluationAgent:
    """
    Analyzes metrics from the ModelEvaluator tool and generates a comprehensive report.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.prompt = get_evaluation_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(EvaluationSummary)

    async def ainvoke(self, state: GraphState, raw_metrics: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Evaluation Agent...")
        
        problem_type = state.get("data_profile", {}).get("problem_type", "Unknown")
        
        # Invoke LLM
        summary: EvaluationSummary = await self.chain.ainvoke({
            "problem_type": problem_type,
            "raw_metrics": str(raw_metrics)
        }, config=config)
        
        return {
            "agent_name": "evaluation_agent",
            "output": summary.model_dump(),
            "validated": True
        }
