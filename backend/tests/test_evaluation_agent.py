# =============================================================================
# backend/tests/test_evaluation_agent.py
#
# Unit tests for the Evaluation tool and agent.
# =============================================================================

import pytest
import os
import joblib
import pandas as pd
from unittest.mock import AsyncMock, patch
from tools.model_evaluator import ModelEvaluator
from agents.evaluation_agent import EvaluationAgent, EvaluationSummary
from graphs.state import GraphState
from sklearn.linear_model import LogisticRegression

@pytest.fixture
def setup_eval_data(tmp_path):
    # Create mock X_test and y_test
    X_test = pd.DataFrame({"f1": [1.0, 2.0], "f2": [2.0, 1.0]})
    y_test = pd.Series([0, 1])
    
    joblib.dump(X_test, str(tmp_path / "X_test.joblib"))
    joblib.dump(y_test, str(tmp_path / "y_test.joblib"))
    
    # Create a mock trained model
    model = LogisticRegression()
    model.fit(X_test, y_test)
    model_path = str(tmp_path / "LogisticRegression_best.joblib")
    joblib.dump(model, model_path)
    
    return str(tmp_path), [model_path]

def test_model_evaluator(setup_eval_data):
    artifact_dir, model_paths = setup_eval_data
    
    evaluator = ModelEvaluator(artifact_dir=artifact_dir)
    results = evaluator.evaluate_models(model_paths, "Classification")
    
    assert "LogisticRegression" in results
    metrics = results["LogisticRegression"]
    assert "accuracy" in metrics
    assert "f1_score" in metrics
    assert "roc_auc" in metrics
    assert "confusion_matrix" in metrics

@pytest.mark.asyncio
@patch("agents.evaluation_agent.ChatOpenAI")
async def test_evaluation_agent(mock_chat_openai):
    mock_summary = EvaluationSummary(
        leaderboard=["LogisticRegression"],
        markdown_report="# Evaluation Report\nLogisticRegression performed perfectly."
    )
    
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_summary)
    mock_structured.ainvoke = AsyncMock(return_value=mock_summary)
    mock_structured.invoke = MagicMock(return_value=mock_summary)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    agent = EvaluationAgent()
    mock_state = GraphState(session_id="test", data_profile={"problem_type": "Classification"})
    
    result = await agent.ainvoke(mock_state, raw_metrics={"LogisticRegression": {"accuracy": 1.0}})
    
    assert result["agent_name"] == "evaluation_agent"
    assert "leaderboard" in result["output"]
    assert len(result["output"]["leaderboard"]) == 1
