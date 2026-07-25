# =============================================================================
# tests/test_analyzer_agent.py
#
# Unit tests for the Dataset Analyzer Agent.
# =============================================================================

import pytest
import tempfile
import pandas as pd
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel

from agents.analyzer_agent import AnalyzerAgent, DataProfileOutput
from graphs.state import create_initial_state

class MockAnalyzerChatModel(BaseChatModel):
    """A mock LangChain chat model for testing structured output."""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="mock")
        
    def with_structured_output(self, schema, **kwargs):
        from unittest.mock import AsyncMock, MagicMock
        mock_profile = DataProfileOutput(
            row_count=3,
            column_count=2,
            columns=["age", "is_churn"],
            dtypes={"age": "int64", "is_churn": "bool"},
            missing_pct={"age": 0.0, "is_churn": 0.0},
            numeric_columns=["age"],
            categorical_columns=["is_churn"],
            datetime_columns=[],
            duplicate_rows=0,
            memory_usage_mb=0.01,
            target_candidates=["is_churn"],
            class_imbalance={"is_churn": "Balanced"},
            potential_problems=[]
        )
        mock_chain = AsyncMock(return_value=mock_profile)
        mock_chain.ainvoke = AsyncMock(return_value=mock_profile)
        mock_chain.invoke = MagicMock(return_value=mock_profile)
        return mock_chain

@pytest.fixture
def dummy_dataset_path():
    """Create a temporary CSV file for testing pandas extraction."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("age,is_churn\n25,True\n30,False\n45,True")
        temp_path = f.name
    yield temp_path
    import os
    os.remove(temp_path)

@pytest.mark.asyncio
async def test_analyzer_agent_success(dummy_dataset_path):
    """Test that the agent reads the file, parses stats, and returns a valid profile."""
    # 1. Setup
    mock_llm = MockAnalyzerChatModel()
    agent = AnalyzerAgent(llm=mock_llm)
    
    state = create_initial_state(
        session_id="test-sess",
        user_id="test-user",
        user_goal="Analyze churn",
        dataset_id="ds-123",
        dataset_path=dummy_dataset_path
    )
    
    # 2. Execute
    update = await agent.generate_profile(state)
    
    # 3. Assertions
    assert update is not None
    assert "data_profile" in update
    profile = update["data_profile"]
    
    assert profile["row_count"] == 3
    assert profile["column_count"] == 2
    assert profile["columns"] == ["age", "is_churn"]
    assert profile["target_column"] == "is_churn"
    
    assert "metadata" in update
    assert "analyzer_insights" in update["metadata"]
    insights = update["metadata"]["analyzer_insights"]
    assert insights["duplicate_rows"] == 0
    assert "is_churn" in insights["target_candidates"]

@pytest.mark.asyncio
async def test_analyzer_agent_retry_handling():
    """Test that the agent's tenacity @retry decorator works upon failure."""
    # Create a mock LLM chain that fails twice then succeeds
    mock_chain = AsyncMock()
    mock_chain.ainvoke.side_effect = [
        RuntimeError("API Timeout"),
        RuntimeError("Rate Limit Exceeded"),
        DataProfileOutput(
            row_count=1, column_count=1, columns=["col1"], dtypes={"col1": "int"},
            missing_pct={"col1": 0.0}, numeric_columns=[], categorical_columns=[],
            datetime_columns=[], duplicate_rows=0, memory_usage_mb=0.0,
            target_candidates=[], class_imbalance={}, potential_problems=[]
        )
    ]
    
    mock_llm = MockAnalyzerChatModel()
    agent = AnalyzerAgent(llm=mock_llm)
    agent.chain = mock_chain # Override with our side-effect chain
    
    # Execute just the retry method
    result = await agent._invoke_llm_with_retry('{"fake": "stats"}')
    
    # Assert it succeeded on the 3rd attempt
    assert result.row_count == 1
    assert mock_chain.ainvoke.call_count == 3
