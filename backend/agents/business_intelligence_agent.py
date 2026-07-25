# =============================================================================
# backend/agents/business_intelligence_agent.py
#
# Agent 2: Business Intelligence Agent. Infers business domain and KPIs.
# =============================================================================

import logging
import json
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from graphs.state import GraphState, BusinessContextDict

log = logging.getLogger(__name__)

class BusinessContextOutput(BaseModel):
    domain: str = Field(..., description="Inferred business domain (e.g. Retail, Healthcare, Finance, Energy, IoT)")
    key_metrics: List[str] = Field(..., description="Top 3-4 key performance indicators (KPIs) to track in this domain.")
    narrative_goals: List[str] = Field(..., description="2-3 analysis goals for this specific domain dataset.")

BI_SYSTEM_PROMPT = """You are a Senior Business Intelligence Consultant.
Your task is to analyze the dataset profile (column names, types, cardinalities, sample values) and infer the business domain, key performance metrics, and narrative analysis goals.

Inputs:
Dataset Profile: {data_profile}
User Goal: {user_goal}

Provide a structured JSON output reflecting the domain, KPIs, and analysis goals.
"""

class BusinessIntelligenceAgent:
    def __init__(self, model_name: str = "gpt-4o"):
        self.llm = ChatOpenAI(model=model_name, temperature=0.1)
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", BI_SYSTEM_PROMPT),
            ("user", "Infer the business context.")
        ])
        self.chain = self.prompt | self.llm.with_structured_output(BusinessContextOutput)

    async def infer_context(self, state: GraphState) -> BusinessContextDict:
        log.info("Running Business Intelligence Agent (Agent 2)...")
        data_profile = state.get("data_profile", {})
        user_goal = state.get("user_goal", "")
        
        profile_str = json.dumps(data_profile, indent=2, default=str)
        
        result: BusinessContextOutput = await self.chain.ainvoke({
            "data_profile": profile_str,
            "user_goal": user_goal
        })
        
        return {
            "domain": result.domain,
            "key_metrics": result.key_metrics,
            "narrative_goals": result.narrative_goals
        }
