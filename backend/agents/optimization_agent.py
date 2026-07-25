# =============================================================================
# backend/agents/optimization_agent.py
#
# The LangChain agent that analyzes if optimization is needed.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.optimization_prompts import get_optimization_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class OptimizationPlan(BaseModel):
    requires_optimization: bool = Field(..., description="True if Optuna should run, False to skip.")
    strategies: List[str] = Field(..., description="List of strategies like 'Hyperparameter Optimization'.")
    reasoning: str = Field(..., description="Why optimization is needed or skipped.")
    markdown_report: str = Field(..., description="Markdown report summarizing the optimization decision.")

class OptimizationAgent:
    """
    Decides whether to run Optuna and what strategies to employ based on eval metrics.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.prompt = get_optimization_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(OptimizationPlan)

    async def ainvoke(self, state: GraphState, winning_model: str, metrics: Dict[str, Any], config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Optimization Agent...")
        
        problem_type = state.get("data_profile", {}).get("problem_type", "Unknown")
        
        plan: OptimizationPlan = await self.chain.ainvoke({
            "winning_model": winning_model,
            "problem_type": problem_type,
            "metrics": str(metrics)
        }, config=config)
        
        return {
            "agent_name": "optimization_agent",
            "output": plan.model_dump(),
            "validated": True
        }
