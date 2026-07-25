# =============================================================================
# tests/test_problem_detection_agent.py
#
# Tests for the Problem Detection Agent.
# =============================================================================

import pytest
from unittest.mock import AsyncMock

from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel

from agents.problem_detection_agent import ProblemDetectionAgent, ProblemDetectionOutput
from graphs.state import create_initial_state

class MockProblemChatModel(BaseChatModel):
    """A mock LangChain chat model that returns a hardcoded problem detection output."""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="mock")
        
    def with_structured_output(self, schema, **kwargs):
        from unittest.mock import AsyncMock, MagicMock
        mock_out = ProblemDetectionOutput(
            problem_type="Classification",
            confidence_score=0.95,
            reasoning="The user goal asks to predict 'churn', which is a discrete categorical label with 2 classes.",
            recommended_target="is_churn"
        )
        mock_chain = AsyncMock(return_value=mock_out)
        mock_chain.ainvoke = AsyncMock(return_value=mock_out)
        mock_chain.invoke = MagicMock(return_value=mock_out)
        return mock_chain

@pytest.mark.asyncio
async def test_problem_detection_agent_success():
    """
    Test that the ProblemDetectionAgent correctly invokes the LLM,
    parses the output, and updates the data_profile properly.
    """
    # 1. Setup
    mock_llm = MockProblemChatModel()
    agent = ProblemDetectionAgent(llm=mock_llm)
    
    initial_state = create_initial_state(
        session_id="test-session-123",
        user_id="test-user-456",
        user_goal="Predict if a customer will churn based on activity.",
        dataset_id="test-dataset-789",
        dataset_path="/tmp/test.csv"
    )
    
    # Inject fake data profile to test dict preservation
    initial_state["data_profile"] = {
        "row_count": 1000,
        "columns": ["id", "activity", "is_churn"],
        "target_column": None, # Should be updated
        "problem_type": None   # Should be updated
    }
    
    # 2. Execute
    update = await agent.detect_problem(initial_state)
    
    # 3. Assertions
    assert update is not None
    assert "data_profile" in update
    
    # Check that previous keys are preserved
    assert update["data_profile"]["row_count"] == 1000
    
    # Check that new keys are updated
    assert update["data_profile"]["problem_type"] == "Classification"
    assert update["data_profile"]["target_column"] == "is_churn"
    
    # Check execution results
    assert "execution_results" in update
    res = update["execution_results"]["problem_detection_node"]
    assert res["confidence_score"] == 0.95
    assert "categorical label" in res["reasoning"]

@pytest.mark.asyncio
async def test_problem_detection_validation():
    """Test that the Pydantic model correctly rejects invalid problem types."""
    with pytest.raises(ValueError, match="must be one of"):
        ProblemDetectionOutput(
            problem_type="InvalidType",
            confidence_score=0.9,
            reasoning="Testing failure",
            recommended_target=None
        )
        
    with pytest.raises(ValueError, match="must be between 0.0 and 1.0"):
        ProblemDetectionOutput(
            problem_type="Regression",
            confidence_score=1.5,
            reasoning="Testing failure",
            recommended_target=None
        )
