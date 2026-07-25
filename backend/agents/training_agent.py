# =============================================================================
# backend/agents/training_agent.py
#
# The LangChain agent that generates the final training summary report.
# =============================================================================

import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.training_prompts import get_training_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

class TrainingSummary(BaseModel):
    winning_model: str = Field(..., description="The name of the algorithm that won.")
    markdown_report: str = Field(..., description="A professional markdown summary of the training results.")

class TrainingSummaryAgent:
    """
    Analyzes metrics from the ModelTrainer and generates a final report.
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.2)
        self.prompt = get_training_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(TrainingSummary)

    async def ainvoke(self, state: GraphState, training_results: List[Dict[str, Any]], config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Training Summary Agent...")
        
        problem_type = state.get("data_profile", {}).get("problem_type", "Unknown")
        
        # Invoke LLM
        summary: TrainingSummary = await self.chain.ainvoke({
            "problem_type": problem_type,
            "training_results": str(training_results)
        }, config=config)
        
        return {
            "agent_name": "training_agent",
            "output": summary.model_dump(),
            "validated": True
        }
