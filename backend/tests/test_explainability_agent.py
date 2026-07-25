# =============================================================================
# backend/tests/test_explainability_agent.py
#
# Unit tests for the Explainability tool and agent.
# =============================================================================

import pytest
import os
import joblib
import pandas as pd
import numpy as np
from unittest.mock import AsyncMock, patch
from tools.model_explainer import ModelExplainer
from agents.explainability_agent import ExplainabilityAgent, ExplainabilitySummary
from graphs.state import GraphState
from sklearn.linear_model import LogisticRegression

@pytest.fixture
def setup_explain_data(tmp_path):
    # Mock data
    X_test = pd.DataFrame({"age": [25, 45, 65], "income": [50000, 100000, 75000]})
    y_test = pd.Series([0, 1, 0])
    
    joblib.dump(X_test, str(tmp_path / "X_test.joblib"))
    joblib.dump(y_test, str(tmp_path / "y_test.joblib"))
    
    # Mock model
    model = LogisticRegression()
    model.fit(X_test, y_test)
    joblib.dump(model, str(tmp_path / "LogisticRegression_optimized.joblib"))
    
    return str(tmp_path)

def test_model_explainer(setup_explain_data):
    artifact_dir = setup_explain_data
    explainer = ModelExplainer(artifact_dir=artifact_dir)
    
    # Run explainer
    results = explainer.generate_explanations("LogisticRegression", "Classification")
    
    assert "feature_importance" in results
    # Since LogisticRegression is not a tree, it will use Permutation Importance
    assert "age" in results["feature_importance"]
    assert "plots" in results
    assert len(results["plots"]) > 0
    assert os.path.exists(results["plots"][0])

@pytest.mark.asyncio
@patch("agents.explainability_agent.ChatOpenAI")
async def test_explainability_agent(mock_chat_openai):
    mock_summary = ExplainabilitySummary(
        executive_summary="Age is the primary driver of the model.",
        business_insights=["Target older demographics."],
        markdown_report="# Executive Summary\nAge is the primary driver."
    )
    
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_summary)
    mock_structured.ainvoke = AsyncMock(return_value=mock_summary)
    mock_structured.invoke = MagicMock(return_value=mock_summary)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    agent = ExplainabilityAgent()
    mock_state = GraphState(session_id="test")
    
    result = await agent.ainvoke(mock_state, {"age": 0.5, "income": 0.1})
    
    assert result["agent_name"] == "explainability_agent"
    assert "executive_summary" in result["output"]
