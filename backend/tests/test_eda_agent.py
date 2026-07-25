# =============================================================================
# tests/test_eda_agent.py
#
# Unit tests for the EDA Agent.
# =============================================================================

import os
import pytest
import tempfile
import pandas as pd
from unittest.mock import AsyncMock, patch

from langchain_core.messages import AIMessage
from langchain_core.language_models import BaseChatModel

from agents.eda_agent import EDAAgent, EDAPlanOutput, PlotRequest, EDAReportOutput
from graphs.state import create_initial_state

class MockEDAChatModel(BaseChatModel):
    """Mock LangChain chat model to simulate the two passes of the EDA Agent."""
    
    @property
    def _llm_type(self) -> str:
        return "mock"
        
    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        return AIMessage(content="mock")
        
    def with_structured_output(self, schema, **kwargs):
        from unittest.mock import AsyncMock, MagicMock
        # Determine which schema we are returning based on the input schema class name
        if schema.__name__ == "EDAPlanOutput":
            mock_val = EDAPlanOutput(
                plots_to_generate=[
                    PlotRequest(
                        plot_type="histogram",
                        columns=["age"],
                        reason="Check distribution of age"
                    )
                ]
            )
        else:
            mock_val = EDAReportOutput(
                markdown_report="# EDA Report\n\nHere is the histogram: [Age Dist](/path/to/plot.html)",
                key_findings=["Age is normally distributed."]
            )
        mock_chain = AsyncMock(return_value=mock_val)
        mock_chain.ainvoke = AsyncMock(return_value=mock_val)
        mock_chain.invoke = MagicMock(return_value=mock_val)
        return mock_chain

@pytest.fixture
def dummy_eda_dataset():
    """Create a temporary CSV file for testing Plotly generation."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("age,income\n25,50000\n30,60000\n45,80000\n35,55000")
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)

@pytest.mark.asyncio
async def test_eda_agent_success(dummy_eda_dataset):
    """Test the full two-pass EDA workflow."""
    # 1. Setup
    mock_llm = MockEDAChatModel()
    agent = EDAAgent(llm=mock_llm)
    
    state = create_initial_state(
        session_id="test-eda-sess",
        user_id="test-user",
        user_goal="Understand income distribution",
        dataset_id="ds-123",
        dataset_path=dummy_eda_dataset
    )
    
    state["data_profile"] = {
        "columns": ["age", "income"],
        "numeric_columns": ["age", "income"]
    }
    
    # 2. Execute
    update = await agent.execute_eda(state)
    
    # 3. Assertions
    assert update is not None
    assert "artifacts" in update
    
    # The python tool should have generated 1 chart based on the mocked plan
    artifacts = update["artifacts"]
    assert len(artifacts) == 1
    assert artifacts[0]["artifact_type"] == "chart"
    assert "histogram" in artifacts[0]["title"]
    assert os.path.exists(artifacts[0]["s3_path"])
    
    # Cleanup the generated artifact
    os.remove(artifacts[0]["s3_path"])
    
    assert "execution_results" in update
    eda_results = update["execution_results"]["eda_node"]
    assert "Age is normally distributed." in eda_results["key_findings"]
    assert "# EDA Report" in eda_results["report"]
