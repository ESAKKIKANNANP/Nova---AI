# =============================================================================
# backend/tests/test_model_selection_agent.py
#
# Unit tests for the Model Selection Agent.
# =============================================================================

import pytest
from unittest.mock import AsyncMock, patch
from graphs.state import GraphState
from agents.model_selection_agent import ModelSelectionAgent, ModelSelectionPlan, CandidateModel

@pytest.mark.asyncio
@patch("agents.model_selection_agent.ChatOpenAI")
async def test_model_selection_agent(mock_chat_openai):
    """Test that the Model Selection Agent correctly returns a ranked JSON list of models."""
    
    # Create mock return from LLM
    mock_plan = ModelSelectionPlan(
        selected_models=[
            CandidateModel(
                model_name="LGBMClassifier",
                reasoning="Fast for large datasets and handles tabular data exceptionally well.",
                suitability_score=9.5,
                hyperparameter_search_space={"n_estimators": [100, 200], "learning_rate": [0.01, 0.1]}
            ),
            CandidateModel(
                model_name="RandomForestClassifier",
                reasoning="Robust baseline, prevents overfitting.",
                suitability_score=8.0,
                hyperparameter_search_space={"n_estimators": [100, 200]}
            )
        ]
    )
    
    # Mock the LLM's with_structured_output behavior
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_plan)
    mock_structured.ainvoke = AsyncMock(return_value=mock_plan)
    mock_structured.invoke = MagicMock(return_value=mock_plan)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    # Initialize Agent
    agent = ModelSelectionAgent()
    
    # Setup mock State
    mock_state = GraphState(
        session_id="test-session",
        data_profile={"problem_type": "Classification", "row_count": 100000},
        user_goal="Maximize accuracy"
    )
    
    # Invoke Agent
    result = await agent.ainvoke(mock_state)
    assert result["agent_name"] == "model_selection_agent"
    assert result["validated"] is True
    
    output = result["output"]
    assert len(output["selected_models"]) == 2
    assert output["selected_models"][0]["model_name"] == "LGBMClassifier"
    assert output["selected_models"][0]["suitability_score"] == 9.5
