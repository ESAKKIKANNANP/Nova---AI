# =============================================================================
# backend/agents/model_selection_agent.py
#
# The LangChain agent that selects and ranks candidate ML algorithms.
# =============================================================================

import logging
from typing import List, Literal, Any, Dict
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.model_selection_prompts import get_model_selection_prompt
from graphs.state import GraphState

from agents.ml_model_registry import get_supported_models

log = logging.getLogger(__name__)

class CandidateModel(BaseModel):
    model_name: str = Field(..., description="The exact class name of the algorithm.")
    reasoning: str = Field(..., description="Explanation of why this algorithm is suitable based on the data and criteria.")
    suitability_score: float = Field(..., description="A score from 0.0 to 10.0 indicating how suitable it is.")
    hyperparameter_search_space: Dict[str, Any] = Field(
        ..., 
        description="A basic dictionary of hyperparameters to tune. Keys are parameter names, values are lists of candidate values."
    )

class ModelSelectionPlan(BaseModel):
    selected_models: List[CandidateModel] = Field(
        ..., 
        description="Ranked list of candidate models (highest suitability first)."
    )

    @field_validator('selected_models')
    def sort_by_score(cls, v):
        return sorted(v, key=lambda x: x.suitability_score, reverse=True)

class ModelSelectionAgent:
    """
    Agent responsible for selecting candidate algorithms based on dataset metadata.
    Outputs a structured JSON blueprint (ModelSelectionPlan).
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.prompt = get_model_selection_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(ModelSelectionPlan)

    async def ainvoke(self, state: GraphState, config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Model Selection Agent...")
        
        data_profile = state.get("data_profile", {})
        task_type = state.get("task_type", "classification")
        user_goal = state.get("user_goal", "Optimize for predictive accuracy.")
        
        # Determine allowed models dynamically
        allowed = get_supported_models(task_type)
        allowed_str = ", ".join(f'"{m}"' for m in allowed)
        
        # Invoke LLM
        plan: ModelSelectionPlan = await self.chain.ainvoke({
            "data_profile": str(data_profile),
            "problem_type": task_type,
            "allowed_models": allowed_str,
            "user_goal": user_goal
        }, config=config)
        
        return {
            "agent_name": "model_selection_agent",
            "output": plan.model_dump(),
            "validated": True
        }
