# =============================================================================
# backend/tests/test_e2e_pipeline.py
#
# Complete End-to-End integration test of the Autonomous Data Scientist pipeline.
# =============================================================================

import pytest
import os
import pandas as pd
import joblib
from unittest.mock import AsyncMock, patch
from sklearn.datasets import make_classification

from graphs.main_graph import build_graph
from graphs.state import GraphState

# Define mock schemas directly for test mock inputs
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class AnalysisPlan(BaseModel):
    understanding: str
    steps: List[str]
    focus_areas: List[str]
    target_variable: str
    is_valid: bool

class DatasetProfile(BaseModel):
    row_count: int
    column_count: int
    columns: List[str]
    data_types: Dict[str, str]
    target_candidates: List[str]
    missing_values: Dict[str, int]
    duplicate_rows: int
    numeric_columns: List[str]
    categorical_columns: List[str]
    datetime_columns: List[str]
    memory_usage: str
    class_imbalance: Dict[str, str]
    potential_problems: List[str]

class CleaningBlueprint(BaseModel):
    actions: List[Any]
    reasoning: str
    is_clean: bool

class EDABlueprint(BaseModel):
    plots: List[Any]
    summary: str

class ProblemDetectionResult(BaseModel):
    problem_type: str
    target_column: str
    confidence_score: float
    reasoning: str

class TransformationStep(BaseModel):
    column: str
    transformation: str
    reasoning: str

class FeatureEngineeringBlueprint(BaseModel):
    transformations: List[TransformationStep]
    reasoning: str

# Import other existing models
from agents.model_selection_agent import ModelSelectionPlan, CandidateModel
from agents.training_agent import TrainingSummary
from agents.evaluation_agent import EvaluationSummary
from agents.optimization_agent import OptimizationPlan
from agents.explainability_agent import ExplainabilitySummary
from agents.business_insight_agent import BusinessInsightReport

@pytest.fixture
def e2e_dataset(tmp_path):
    # Generate synthetic data
    X, y = make_classification(n_samples=100, n_features=5, n_classes=2, random_state=42)
    df = pd.DataFrame(X, columns=[f"feature_{i}" for i in range(5)])
    df["target"] = y
    
    csv_path = str(tmp_path / "e2e_dataset.csv")
    df.to_csv(csv_path, index=False)
    
    # We must also mock the pipeline artifact early on for training since some nodes need it
    # We'll mock it inside the feature_node
    
    return csv_path, str(tmp_path)

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI")
async def test_full_pipeline_execution(mock_llm_class, e2e_dataset):
    """
    Runs the full LangGraph pipeline end-to-end with local mock models.
    We mock the ChatOpenAI class to return valid Pydantic models for every agent,
    allowing the deterministic tools (pandas, sklearn, optuna, mlflow) to execute for real.
    """
    import sys
    # Propagate the mock ChatOpenAI class to all loaded agent modules
    for module_name, module in list(sys.modules.items()):
        if "agent" in module_name:
            if hasattr(module, "ChatOpenAI"):
                setattr(module, "ChatOpenAI", mock_llm_class)

    csv_path, tmp_dir = e2e_dataset
    
    # --- MOCK SETUP ---
    from unittest.mock import MagicMock, AsyncMock
    mock_instance = MagicMock()

    def mock_with_structured_output(schema, **kwargs):
        name = schema.__name__ if hasattr(schema, "__name__") else str(schema)
        
        if "AnalysisPlan" in name:
            val = AnalysisPlan(
                understanding="E2E Test",
                steps=["Load", "Clean"],
                focus_areas=["Accuracy"],
                target_variable="target",
                is_valid=True
            )
        elif "DatasetProfile" in name:
            val = DatasetProfile(
                row_count=100, column_count=6, columns=["feature_0", "feature_1", "feature_2", "feature_3", "feature_4", "target"],
                data_types={"feature_0": "float64"}, target_candidates=["target"],
                missing_values={}, duplicate_rows=0, numeric_columns=["feature_0", "target"],
                categorical_columns=[], datetime_columns=[], memory_usage="1KB",
                class_imbalance={}, potential_problems=[]
            )
        elif "CleaningBlueprint" in name:
            val = CleaningBlueprint(actions=[], reasoning="No cleaning needed", is_clean=True)
        elif "EDABlueprint" in name:
            val = EDABlueprint(plots=[], summary="EDA Summary")
        elif "ProblemDetectionResult" in name or "ProblemDetectionOutput" in name:
            val = ProblemDetectionResult(problem_type="Classification", target_column="target", confidence_score=0.99, reasoning="Binary target")
        elif "FeatureEngineeringBlueprint" in name or "FeatureEngineeringPlan" in name:
            from agents.feature_engineering_agent import FeatureEngineeringPlan, FeatureTransformation
            val = FeatureEngineeringPlan(
                transformations=[
                    FeatureTransformation(columns=["feature_0"], operation="Standard Scaling", reasoning="Scale")
                ],
                drop_columns=[]
            )
        elif "ModelSelectionPlan" in name:
            val = ModelSelectionPlan(
                selected_models=[
                    CandidateModel(
                        model_name="RandomForestClassifier",
                        reasoning="Fast",
                        suitability_score=9.0,
                        hyperparameter_search_space={"n_estimators": [10]}
                    )
                ]
            )
        elif "TrainingSummary" in name:
            val = TrainingSummary(winning_model="RandomForestClassifier", markdown_report="Trained")
        elif "EvaluationSummary" in name:
            val = EvaluationSummary(leaderboard=["RandomForestClassifier"], markdown_report="Eval")
        elif "OptimizationPlan" in name:
            val = OptimizationPlan(requires_optimization=False, strategies=[], reasoning="Skipping", markdown_report="Skipped")
        elif "ExplainabilitySummary" in name:
            val = ExplainabilitySummary(executive_summary="Expl", business_insights=["B1"], markdown_report="Explain")
        elif "BusinessInsightReport" in name:
            val = BusinessInsightReport(executive_summary="Exec", business_insights=["B"], recommendations=["R"], risk_analysis=["R"], next_steps=["N"])
        elif "ReportData" in name:
            from agents.report_generation_agent import ReportData
            val = ReportData(
                executive_summary="Exec",
                dataset_overview="Overview",
                eda_summary="EDA",
                feature_engineering="Features",
                model_comparison="Compare",
                evaluation_metrics="Metrics",
                explainability="Explain",
                business_insights=["Insight"],
                recommendations=["Rec"],
                appendix="Appendix"
            )
        else:
            val = MagicMock()
            
        mock_chain = AsyncMock(return_value=val)
        mock_chain.ainvoke = AsyncMock(return_value=val)
        mock_chain.invoke = MagicMock(return_value=val)
        return mock_chain

    mock_instance.with_structured_output.side_effect = mock_with_structured_output
    mock_llm_class.return_value = mock_instance
    
    # --- GRAPH EXECUTION ---
    app = build_graph()
    
    initial_state = GraphState(
        session_id="e2e_test",
        user_request="Build a model for target.",
        dataset_path=csv_path,
        optimization_attempts=0,
        max_optimization_attempts=3,
        target_metric_threshold=0.95
    )
    
    # We must configure the thread config for the checkpointer
    config = {"configurable": {"thread_id": "e2e_thread_1"}}
    
    # Execute the graph asynchronously
    final_state = await app.ainvoke(initial_state, config=config)
    
    # --- ASSERTIONS ---
    assert final_state["is_complete"] is True
    assert final_state["current_node"] == "report_node"
    
    # Assert artifacts were created
    artifacts = final_state.get("artifacts", [])
    assert len(artifacts) > 0
    
    artifact_types = [a["artifact_type"] for a in artifacts]
    assert "model" in artifact_types # The winning model from training
    assert "report_md" in artifact_types # Final insight report
    assert "report_pdf" in artifact_types # Final insight report
    
    # Verify MLflow DB exists in the local directory
    assert os.path.exists("mlruns")
