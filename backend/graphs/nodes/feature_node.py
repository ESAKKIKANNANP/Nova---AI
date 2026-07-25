# =============================================================================
# graphs/nodes/feature_node.py
#
# Stub node for Feature Engineering.
# =============================================================================

import logging
import pandas as pd
from graphs.state import GraphState
from agents.feature_engineering_agent import FeatureEngineeringAgent
from tools.pipeline_builder import PipelineBuilder

log = logging.getLogger(__name__)

async def feature_node(state: GraphState) -> GraphState:
    log.info(f"Executing feature_node for session: {state.get('session_id')}")
    
    agent = FeatureEngineeringAgent()
    builder = PipelineBuilder()
    
    # 1. Ask LLM for the feature engineering blueprint
    agent_output = await agent.ainvoke(state)
    blueprint = agent_output["output"]
    
    # 2. Execute the deterministic tool to build the scikit-learn pipeline
    dataset_path = state.get("dataset_path")
    pipeline_path = None
    
    if dataset_path and dataset_path.endswith(".csv"):
        try:
            df = pd.read_csv(dataset_path)
            target_col = state.get("data_profile", {}).get("target_column")
            pipeline_path = builder.build_and_fit(df, blueprint, target_col)
        except Exception as e:
            log.error(f"Pipeline Builder failed: {str(e)}")
    
    # 3. Save artifacts to state
    new_artifacts = []
    if pipeline_path:
        new_artifacts.append({
            "artifact_id": f"pipeline-{state.get('session_id')}",
            "artifact_type": "model",
            "s3_path": pipeline_path,
            "mime_type": "application/octet-stream",
            "title": "Feature Engineering Pipeline (Joblib)"
        })
    
    return {
        "current_node": "feature_node",
        "agent_outputs": [agent_output],
        "artifacts": new_artifacts,
        "execution_results": {"feature_node": {"blueprint": blueprint, "pipeline_path": pipeline_path}}
    }
