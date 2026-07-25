# =============================================================================
# backend/agents/feature_engineering_agent.py
#
# The LangChain agent that designs the Feature Engineering Pipeline.
# =============================================================================

import logging
from typing import List, Literal, Any, Dict
from pydantic import BaseModel, Field, field_validator
from langchain_openai import ChatOpenAI
from langchain_core.runnables import RunnableConfig

from prompts.feature_engineering_prompts import get_feature_engineering_prompt
from graphs.state import GraphState

log = logging.getLogger(__name__)

# Allowed operations matching the scikit-learn builder capabilities
AllowedOperations = Literal[
    "One-Hot Encoding", "Label Encoding", "Target Encoding", 
    "Standard Scaling", "MinMax Scaling", "Robust Scaling", 
    "Polynomial Features", "Feature Interactions", "Datetime Feature Extraction", 
    "Text Vectorization", "Missing Value Indicators", "Feature Selection"
]

class FeatureTransformation(BaseModel):
    columns: List[str] = Field(..., description="List of column names to apply this transformation to.")
    operation: AllowedOperations = Field(..., description="The transformation operation to apply.")
    reasoning: str = Field(..., description="Detailed explanation of why this transformation was chosen.")

class FeatureEngineeringPlan(BaseModel):
    transformations: List[FeatureTransformation] = Field(
        ..., 
        description="Ordered list of feature engineering transformations to apply."
    )
    drop_columns: List[str] = Field(
        default_factory=list, 
        description="Columns that should be explicitly dropped before training."
    )
    
    @field_validator('transformations')
    def validate_transformations(cls, v):
        if not v:
            raise ValueError("At least one transformation must be specified.")
        return v

class FeatureEngineeringAgent:
    """
    Agent responsible for designing the ML feature engineering pipeline based on the data profile.
    Outputs a structured JSON blueprint (FeatureEngineeringPlan).
    """
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.prompt = get_feature_engineering_prompt()
        self.chain = self.prompt | self.llm.with_structured_output(FeatureEngineeringPlan)

    async def ainvoke(self, state: GraphState, config: RunnableConfig | None = None) -> Dict[str, Any]:
        log.info("Invoking Feature Engineering Agent...")
        
        data_profile = state.get("data_profile")
        if not data_profile:
            raise ValueError("Data profile is missing from state. Analyzer must run first.")
            
        user_goal = state.get("user_goal", "Optimize features for predictive modeling.")
        
        # Invoke LLM to generate the plan
        plan: FeatureEngineeringPlan = await self.chain.ainvoke({
            "data_profile": str(data_profile),
            "user_goal": user_goal
        }, config=config)
        
        return {
            "agent_name": "feature_engineering_agent",
            "output": plan.model_dump(),
            "validated": True
        }
