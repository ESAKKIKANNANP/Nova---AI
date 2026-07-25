import pytest
import os
import sys
import pandas as pd
from typing import Any
from unittest.mock import AsyncMock, patch, MagicMock
from graphs.main_graph import build_graph
from graphs.state import GraphState, create_initial_state

# Import schemas to mock
from agents.model_selection_agent import ModelSelectionPlan, CandidateModel
from agents.training_agent import TrainingSummary
from agents.evaluation_agent import EvaluationSummary
from agents.explainability_agent import ExplainabilitySummary
from agents.business_insight_agent import BusinessInsightReport
from agents.business_intelligence_agent import BusinessContextOutput
from agents.problem_detection_agent import ProblemDetectionOutput
from agents.analyzer_agent import DataProfileOutput

# Globals to track current test setup dynamically inside the mock wrapper
CURRENT_DATASET = "medical"

class MockedPydanticResponses:
    @staticmethod
    def get_response(schema: Any):
        global CURRENT_DATASET
        schema_name = schema.__name__ if hasattr(schema, "__name__") else str(schema)
        
        if "DataProfileOutput" in schema_name:
            if CURRENT_DATASET == "medical":
                return DataProfileOutput(
                    row_count=10, column_count=5,
                    columns=["patient_id", "age", "blood_pressure", "admit_date", "readmitted"],
                    dtypes={"patient_id": "int64", "age": "int64", "blood_pressure": "int64", "admit_date": "object", "readmitted": "int64"},
                    missing_pct={"patient_id": 0.0, "age": 0.0, "blood_pressure": 0.0, "admit_date": 0.0, "readmitted": 0.0},
                    numeric_columns=["patient_id", "age", "blood_pressure", "readmitted"],
                    categorical_columns=[], datetime_columns=["admit_date"],
                    duplicate_rows=0, memory_usage_mb=0.1,
                    target_candidates=["readmitted"], class_imbalance={}, potential_problems=[],
                    column_roles={"patient_id": "id", "age": "feature", "blood_pressure": "feature", "admit_date": "date", "readmitted": "target"}
                )
            elif CURRENT_DATASET == "sensor":
                return DataProfileOutput(
                    row_count=10, column_count=4,
                    columns=["timestamp", "temperature", "humidity", "voltage"],
                    dtypes={"timestamp": "object", "temperature": "float64", "humidity": "float64", "voltage": "float64"},
                    missing_pct={"timestamp": 0.0, "temperature": 0.0, "humidity": 0.0, "voltage": 0.0},
                    numeric_columns=["temperature", "humidity", "voltage"],
                    categorical_columns=[], datetime_columns=["timestamp"],
                    duplicate_rows=0, memory_usage_mb=0.1,
                    target_candidates=["temperature"], class_imbalance={}, potential_problems=[],
                    column_roles={"timestamp": "date", "temperature": "target", "humidity": "feature", "voltage": "feature"}
                )
            else: # unsupervised
                return DataProfileOutput(
                    row_count=9, column_count=3,
                    columns=["feature_x", "feature_y", "feature_z"],
                    dtypes={"feature_x": "float64", "feature_y": "float64", "feature_z": "float64"},
                    missing_pct={"feature_x": 0.0, "feature_y": 0.0, "feature_z": 0.0},
                    numeric_columns=["feature_x", "feature_y", "feature_z"],
                    categorical_columns=[], datetime_columns=[],
                    duplicate_rows=0, memory_usage_mb=0.1,
                    target_candidates=[], class_imbalance={}, potential_problems=[],
                    column_roles={"feature_x": "feature", "feature_y": "feature", "feature_z": "feature"}
                )
                
        elif "BusinessContextOutput" in schema_name:
            if CURRENT_DATASET == "medical":
                return BusinessContextOutput(
                    domain="Healthcare",
                    key_metrics=["Readmission Rate", "Average Age", "High Blood Pressure Cases"],
                    narrative_goals=["Predict patient readmissions", "Optimize hospital beds"]
                )
            elif CURRENT_DATASET == "sensor":
                return BusinessContextOutput(
                    domain="IoT Sensor Telemetry",
                    key_metrics=["Average Temperature", "Max Voltage Drop", "Humidity Index"],
                    narrative_goals=["Forecast temperature thresholds", "Monitor voltage spikes"]
                )
            else:
                return BusinessContextOutput(
                    domain="Unsupervised Spatial Clustering",
                    key_metrics=["Anomaly Score", "Spatial Centroid Spread"],
                    narrative_goals=["Segment feature coordinates", "Identify density anomalies"]
                )
                
        elif "ProblemDetectionOutput" in schema_name:
            if CURRENT_DATASET == "medical":
                return ProblemDetectionOutput(problem_type="Classification", confidence_score=0.98, reasoning="Target column readmitted has discrete values", recommended_target="readmitted")
            elif CURRENT_DATASET == "sensor":
                return ProblemDetectionOutput(problem_type="Regression", confidence_score=0.95, reasoning="Target temperature is continuous values", recommended_target="temperature")
            else:
                return ProblemDetectionOutput(problem_type="Clustering", confidence_score=0.92, reasoning="No clear target candidates specified", recommended_target=None)
                
        elif "FeatureEngineeringPlan" in schema_name or "FeatureEngineeringBlueprint" in schema_name:
            from agents.feature_engineering_agent import FeatureEngineeringPlan, FeatureTransformation
            if CURRENT_DATASET == "medical":
                return FeatureEngineeringPlan(
                    transformations=[
                        FeatureTransformation(columns=["age", "blood_pressure"], operation="Standard Scaling", reasoning="Normalize numeric features")
                    ],
                    drop_columns=["patient_id"]
                )
            elif CURRENT_DATASET == "sensor":
                return FeatureEngineeringPlan(
                    transformations=[
                        FeatureTransformation(columns=["humidity", "voltage"], operation="Standard Scaling", reasoning="Normalize sensor scale")
                    ],
                    drop_columns=[]
                )
            else: # unsupervised
                return FeatureEngineeringPlan(
                    transformations=[
                        FeatureTransformation(columns=["feature_x", "feature_y", "feature_z"], operation="Standard Scaling", reasoning="Scale spatial features")
                    ],
                    drop_columns=[]
                )
                
        elif "ModelSelectionPlan" in schema_name:
            if CURRENT_DATASET == "medical":
                return ModelSelectionPlan(selected_models=[
                    CandidateModel(model_name="LogisticRegression", reasoning="Baseline linear model", suitability_score=9.0, hyperparameter_search_space={"C": [1.0]}),
                    CandidateModel(model_name="RandomForestClassifier", reasoning="Tree ensemble", suitability_score=8.5, hyperparameter_search_space={"n_estimators": [50]})
                ])
            elif CURRENT_DATASET == "sensor":
                return ModelSelectionPlan(selected_models=[
                    CandidateModel(model_name="LinearRegression", reasoning="Baseline regression", suitability_score=9.0, hyperparameter_search_space={}),
                    CandidateModel(model_name="RandomForestRegressor", reasoning="Tree regression ensemble", suitability_score=8.5, hyperparameter_search_space={"n_estimators": [50]})
                ])
            else:
                return ModelSelectionPlan(selected_models=[
                    CandidateModel(model_name="KMeans", reasoning="Centroid clustering baseline", suitability_score=9.0, hyperparameter_search_space={"n_clusters": [3]})
                ])
                
        elif "TrainingSummary" in schema_name:
            win = "LogisticRegression" if CURRENT_DATASET == "medical" else ("LinearRegression" if CURRENT_DATASET == "sensor" else "KMeans")
            return TrainingSummary(winning_model=win, markdown_report="Summary report complete.")
            
        elif "EvaluationSummary" in schema_name:
            return EvaluationSummary(leaderboard=["Top Model"], markdown_report="Leaderboard scores generated.")
            
        elif "ExplainabilitySummary" in schema_name:
            return ExplainabilitySummary(executive_summary="SHAP summary details", business_insights=["SHAP Insight"], markdown_report="SHAP explanation complete.")
            
        elif "BusinessInsightReport" in schema_name:
            return BusinessInsightReport(executive_summary="Exec summary", business_insights=["Insight 1"], recommendations=["Rec 1"], risk_analysis=["Risk 1"], next_steps=["Step 1"])
            
        elif "ReportData" in schema_name:
            from agents.report_generation_agent import ReportData
            return ReportData(
                executive_summary="Exec", dataset_overview="Overview", eda_summary="EDA",
                feature_engineering="FE", model_comparison="MC", evaluation_metrics="EM",
                explainability="Exp", business_insights=["BI"], recommendations=["Rec"], appendix="App"
            )
            
        # Fallback self-healing dynamic Pydantic initializer
        from pydantic import BaseModel
        if isinstance(schema, type) and issubclass(schema, BaseModel):
            dummy = {}
            for name, field in schema.model_fields.items():
                ftype = field.annotation
                if ftype == str:
                    dummy[name] = "dummy"
                elif ftype == int:
                    dummy[name] = 0
                elif ftype == float:
                    dummy[name] = 0.0
                elif ftype == bool:
                    dummy[name] = False
                elif getattr(ftype, '__origin__', None) == list:
                    dummy[name] = []
                elif getattr(ftype, '__origin__', None) == dict:
                    dummy[name] = {}
                else:
                    dummy[name] = None
            return schema(**dummy)
            
        return {}

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI")
async def test_classification_medical_readmission(mock_llm_class):
    global CURRENT_DATASET
    CURRENT_DATASET = "medical"
    
    # Propagate mock to sub-modules
    for module_name, module in list(sys.modules.items()):
        if ("agent" in module_name or "node" in module_name) and hasattr(module, "ChatOpenAI"):
            setattr(module, "ChatOpenAI", mock_llm_class)
            
    mock_instance = MagicMock()
    mock_instance.with_structured_output.side_effect = lambda schema, **kwargs: AsyncMock(
        return_value=MockedPydanticResponses.get_response(schema)
    )
    mock_llm_class.return_value = mock_instance
    
    app = build_graph()
    state = create_initial_state(
        session_id="test_classification",
        user_id="test_user",
        user_goal="Predict if patient will be readmitted.",
        dataset_id="medical",
        dataset_path="tests/fixtures/medical_readmission.csv",
        dataset_format="csv"
    )
    
    config = {"configurable": {"thread_id": "thread_class"}}
    final_state = await app.ainvoke(state, config=config)
    
    assert final_state["is_complete"] is True
    assert final_state["task_type"] == "classification"
    assert final_state["business_context"]["domain"] == "Healthcare"
    
    # Verify dynamic grid widgets list populated
    widgets = final_state.get("widgets", [])
    assert len(widgets) > 0
    kpis = [w for w in widgets if w["widget_type"] == "kpi"]
    assert len(kpis) == 3
    assert kpis[0]["data_binding_key"] == "Readmission Rate"
    
    # Check cleaning node report output contains actual column name
    cleaning_history = final_state.get("cleaning_history", [])
    assert len(cleaning_history) > 0
    # No missing values in medical CSV fixture, so it verified clean
    assert "verified" in cleaning_history[0].lower() or any("patient_id" in step or "readmitted" in step for step in cleaning_history)

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI")
async def test_regression_sensor_readings(mock_llm_class):
    global CURRENT_DATASET
    CURRENT_DATASET = "sensor"
    
    for module_name, module in list(sys.modules.items()):
        if ("agent" in module_name or "node" in module_name) and hasattr(module, "ChatOpenAI"):
            setattr(module, "ChatOpenAI", mock_llm_class)
            
    mock_instance = MagicMock()
    mock_instance.with_structured_output.side_effect = lambda schema, **kwargs: AsyncMock(
        return_value=MockedPydanticResponses.get_response(schema)
    )
    mock_llm_class.return_value = mock_instance
    
    app = build_graph()
    state = create_initial_state(
        session_id="test_regression",
        user_id="test_user",
        user_goal="Forecast temperature.",
        dataset_id="sensor",
        dataset_path="tests/fixtures/sensor_readings.csv",
        dataset_format="csv"
    )
    
    config = {"configurable": {"thread_id": "thread_reg"}}
    final_state = await app.ainvoke(state, config=config)
    
    assert final_state["is_complete"] is True
    assert final_state["task_type"] == "regression"
    assert final_state["business_context"]["domain"] == "IoT Sensor Telemetry"
    
    widgets = final_state.get("widgets", [])
    assert len(widgets) > 0
    kpis = [w for w in widgets if w["widget_type"] == "kpi"]
    assert len(kpis) == 3
    assert kpis[0]["data_binding_key"] == "Average Temperature"
    
    # Check that model results contains regressor names and appropriate metrics
    model_results = final_state.get("model_results", [])
    assert len(model_results) > 0
    assert "Regression" in model_results[0]["model_name"] or "Regressor" in model_results[0]["model_name"] or "KMeans" in model_results[0]["model_name"] or "Regression" in str(model_results)

@pytest.mark.asyncio
@patch("langchain_openai.ChatOpenAI")
async def test_unsupervised_clustering(mock_llm_class):
    global CURRENT_DATASET
    CURRENT_DATASET = "unsupervised"
    
    for module_name, module in list(sys.modules.items()):
        if ("agent" in module_name or "node" in module_name) and hasattr(module, "ChatOpenAI"):
            setattr(module, "ChatOpenAI", mock_llm_class)
            
    mock_instance = MagicMock()
    mock_instance.with_structured_output.side_effect = lambda schema, **kwargs: AsyncMock(
        return_value=MockedPydanticResponses.get_response(schema)
    )
    mock_llm_class.return_value = mock_instance
    
    app = build_graph()
    state = create_initial_state(
        session_id="test_clustering",
        user_id="test_user",
        user_goal="Cluster feature columns without targets.",
        dataset_id="unsupervised",
        dataset_path="tests/fixtures/unsupervised_clusters.csv",
        dataset_format="csv"
    )
    
    config = {"configurable": {"thread_id": "thread_cluster"}}
    final_state = await app.ainvoke(state, config=config)
    
    assert final_state["is_complete"] is True
    assert final_state["task_type"] == "clustering"
    assert final_state["business_context"]["domain"] == "Unsupervised Spatial Clustering"
    
    # Assert it executes successfully without any target columns
    assert final_state["data_profile"]["target_column"] is None
