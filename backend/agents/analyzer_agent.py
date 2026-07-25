# =============================================================================
# agents/analyzer_agent.py
#
# Dataset Analyzer Agent Implementation
#
# Architecture Decisions:
# 1. Separation of Concerns: The agent uses `data_reader.py` (pandas) to compute
#    deterministic stats (row counts, nulls) safely, rather than hallucinating code.
#    The LLM focuses purely on *interpretation* (finding targets, problems, class imbalance).
# 2. Structured Output: LangChain's `.with_structured_output()` ensures the LLM
#    returns a strict JSON payload matching `DataProfileOutput`.
# 3. Retry Handling: Wrapped with Tenacity (`@retry`) to automatically recover
#    from transient API errors or rate limits.
# 4. State Integration: Returns `DataProfileDict` to update the LangGraph state.
# =============================================================================

import json
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from tenacity import retry, stop_after_attempt, wait_exponential

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.language_models import BaseChatModel

from graphs.state import GraphState, DataProfileDict
from prompts.analyzer_prompts import ANALYZER_SYSTEM_PROMPT
from tools.data_reader import extract_raw_stats

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Output Schemas
# ---------------------------------------------------------------------------

class DataProfileOutput(BaseModel):
    """The structured output expected from the Analyzer LLM."""
    row_count: int = Field(description="Total number of rows")
    column_count: int = Field(description="Total number of columns")
    columns: List[str] = Field(description="List of all column names")
    dtypes: Dict[str, str] = Field(description="Dictionary mapping column name to its data type")
    missing_pct: Dict[str, float] = Field(description="Dictionary mapping column name to percentage of missing values (0-100)")
    
    numeric_columns: List[str] = Field(description="List of numeric columns")
    categorical_columns: List[str] = Field(description="List of categorical columns")
    datetime_columns: List[str] = Field(description="List of datetime columns")
    
    duplicate_rows: int = Field(description="Number of duplicate rows")
    memory_usage_mb: float = Field(description="Memory usage of the dataset in MB")
    
    target_candidates: List[str] = Field(description="List of columns that could serve as prediction targets")
    class_imbalance: Dict[str, str] = Field(description="Analysis of class imbalance for potential categorical targets")
    potential_problems: List[str] = Field(description="List of identified data quality issues (e.g., high nulls, leakage)")
    column_roles: Dict[str, str] = Field(description="Dictionary mapping each column to its role: 'target', 'feature', 'id', 'date', or 'text'.")


# ---------------------------------------------------------------------------
# Agent Implementation
# ---------------------------------------------------------------------------

class AnalyzerAgent:
    """
    The Dataset Analyzer Agent.
    
    Reads raw pandas statistics, interprets them via an LLM, and produces
    a comprehensive structured data profile.
    """
    
    def __init__(self, llm: BaseChatModel):
        self.llm = llm
        
        # Bind the Pydantic schema
        self.structured_llm = self.llm.with_structured_output(DataProfileOutput)
        
        # Create the prompt template
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", ANALYZER_SYSTEM_PROMPT),
            ("user", "Please generate the data profile based on these raw statistics.")
        ])
        
        self.chain = self.prompt | self.structured_llm

    # Retry decorator: retries up to 3 times, exponential backoff starting at 2s
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def _invoke_llm_with_retry(self, raw_stats_str: str) -> DataProfileOutput:
        """Invokes the LLM chain with automatic retry handling."""
        log.info("Invoking Analyzer LLM with structured output...")
        return await self.chain.ainvoke({"raw_stats": raw_stats_str})

    async def generate_profile(self, state: GraphState) -> DataProfileDict:
        """
        Execute the analysis on the dataset defined in the state.
        
        Args:
            state: The current LangGraph state.
            
        Returns:
            A DataProfileDict suitable for updating the state.
        """
        session_id = state.get("session_id", "unknown")
        dataset_path = state.get("dataset_path")
        
        log.info(f"Analyzer Agent started for session {session_id}")
        
        if not dataset_path:
            raise ValueError("dataset_path is missing from the state. Cannot analyze.")
            
        try:
            # 1. Extract deterministic stats using the tool (pandas)
            raw_stats = extract_raw_stats(dataset_path)
            raw_stats_str = json.dumps(raw_stats, indent=2, default=str)
            
            # 2. Ask LLM to interpret the stats and return structured JSON
            result: DataProfileOutput = await self._invoke_llm_with_retry(raw_stats_str)
            
            # Build column profiles
            column_profiles = {}
            for col in result.columns:
                column_profiles[col] = {
                    "dtype": result.dtypes.get(col, "object"),
                    "cardinality": raw_stats.get("cardinalities", {}).get(col, 0),
                    "null_pct": result.missing_pct.get(col, 0.0),
                    "sample_values": raw_stats.get("sample_values", {}).get(col, []),
                    "role": result.column_roles.get(col, "feature")
                }

            # 3. Map Pydantic output to TypedDict for GraphState
            profile_dict: DataProfileDict = {
                "row_count": result.row_count,
                "column_count": result.column_count,
                "columns": result.columns,
                "dtypes": result.dtypes,
                "missing_pct": result.missing_pct,
                # In a real app, numeric/categorical summaries would be appended here 
                # directly from the raw_stats to avoid LLM hallucination of heavy numerical data.
                "numeric_summary": raw_stats.get("numeric_summary", {}),
                "categorical_summary": raw_stats.get("categorical_summary", {}),
                "target_column": result.target_candidates[0] if result.target_candidates else None,
                "problem_type": None,  # Left for Planner or ML Agent to refine
                "column_profiles": column_profiles
            }
            
            # Add extra analysis fields to metadata for later agents
            extra_metadata = {
                "analyzer_insights": {
                    "duplicate_rows": result.duplicate_rows,
                    "memory_usage_mb": result.memory_usage_mb,
                    "target_candidates": result.target_candidates,
                    "class_imbalance": result.class_imbalance,
                    "potential_problems": result.potential_problems,
                    "numeric_columns": result.numeric_columns,
                    "categorical_columns": result.categorical_columns,
                    "datetime_columns": result.datetime_columns
                }
            }
            
            log.info("Analyzer Agent completed successfully.")
            
            # Return partial state update
            return {
                "data_profile": profile_dict,
                "metadata": extra_metadata
            }
            
        except Exception as exc:
            log.error(f"Analyzer Agent failed: {str(exc)}")
            raise RuntimeError(f"Analyzer Agent failed: {str(exc)}")
