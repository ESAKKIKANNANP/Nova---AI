# =============================================================================
# agents/problem_detection_agent.py
#
# Problem Detection Agent Implementation
#
# Architecture Decisions:
# 1. Specialized Expert Agent: Dedicated strictly to mapping the user's raw goal
#    and the analyzer's raw profile to a formal ML task (Classification, Regression, etc.).
# 2. Structured Output: Uses LangChain's `.with_structured_output()` to guarantee
#    strict enum-like problem types and valid float confidence scores.
# 3. State Update: Modifies the `problem_type` in the `data_profile` state dict,
#    enabling the downstream Planner or ML Builder agents to branch their logic
#    accordingly.
# =============================================================================

import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from graphs.state import GraphState

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output Schemas
# ---------------------------------------------------------------------------

class ProblemDetectionOutput(BaseModel):
    """The structured output expected from the Problem Detection LLM."""
    
    problem_type: str = Field(
        description="Must be exactly one of: Classification, Regression, Clustering, Time Series, Recommendation"
    )
    confidence_score: float = Field(
        description="A confidence score between 0.0 and 1.0"
    )
    reasoning: str = Field(
        description="Detailed explanation of why this problem type was chosen based on the user goal and dataset profile"
    )
    recommended_target: Optional[str] = Field(
        default=None,
        description="The recommended column to use as the prediction target, if applicable (None for Clustering)"
    )

    @validator("problem_type")
    def validate_problem_type(cls, v):
        allowed = ["Classification", "Regression", "Clustering", "Time Series", "Recommendation"]
        if v not in allowed:
            raise ValueError(f"problem_type must be one of {allowed}, got {v}")
        return v
        
    @validator("confidence_score")
    def validate_confidence(cls, v):
        if not (0.0 <= v <= 1.0):
            raise ValueError(f"confidence_score must be between 0.0 and 1.0, got {v}")
        return v


# ---------------------------------------------------------------------------
# Agent Implementation
# ---------------------------------------------------------------------------

class ProblemDetectionAgent:
    """
    The Problem Detection Agent.
    
    Determines the formal ML problem type based on the user's natural language
    goal and the raw data profile extracted previously.
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        
        # Bind the Pydantic schema to force structured output with validation
        self.structured_llm = self.llm.with_structured_output(ProblemDetectionOutput)
        
        from backend.prompts.problem_detection_prompts import PROBLEM_DETECTION_PROMPT
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", PROBLEM_DETECTION_PROMPT),
            ("user", "Determine the Machine Learning problem type.")
        ])
        
        self.chain = self.prompt | self.structured_llm

    async def detect_problem(self, state: GraphState) -> Dict[str, Any]:
        """
        Executes the problem detection workflow.
        
        Args:
            state: The current LangGraph state containing goal and profile.
            
        Returns:
            Partial state update patching the problem_type in data_profile.
        """
        session_id = state.get("session_id", "unknown_session")
        user_goal = state.get("user_goal", "")
        data_profile = state.get("data_profile") or {}
        
        log.info(f"Problem Detection Agent started for session: {session_id}")
        
        if not user_goal and not data_profile:
            raise ValueError("Both user_goal and data_profile are missing. Cannot detect problem.")
            
        profile_str = json.dumps(data_profile, indent=2) if data_profile else "No data profile available."
        
        try:
            # Execute the LangChain pipeline
            result: ProblemDetectionOutput = await self.chain.ainvoke({
                "user_goal": user_goal,
                "data_profile": profile_str
            })
            
            log.info(f"Detected problem type: {result.problem_type} with confidence {result.confidence_score}")
            
            # Prepare state update
            # We preserve existing profile keys and just update the problem_type and target
            updated_profile = dict(data_profile)
            updated_profile["problem_type"] = result.problem_type
            
            if result.recommended_target:
                updated_profile["target_column"] = result.recommended_target
                
            # Log results to execution_results for visibility
            execution_results = {
                "problem_detection_node": {
                    "problem_type": result.problem_type,
                    "confidence_score": result.confidence_score,
                    "reasoning": result.reasoning,
                    "recommended_target": result.recommended_target
                }
            }
            
            return {
                "data_profile": updated_profile,
                "execution_results": execution_results
            }
            
        except Exception as exc:
            log.error(f"Failed to detect problem type: {str(exc)}")
            raise RuntimeError(f"Problem Detection Agent failed: {str(exc)}")
