# =============================================================================
# backend/tests/test_report_generation_agent.py
#
# Unit tests for the Report Generation Agent and Endpoints.
# =============================================================================

import pytest
import os
from unittest.mock import AsyncMock, patch
from tools.report_formatter import ReportFormatter
from agents.report_generation_agent import ReportGenerationAgent, ReportData
from graphs.state import GraphState
from fastapi.testclient import TestClient
from api.v1.endpoints.reports import router

# A mini test app just for this router
from fastapi import FastAPI
app = FastAPI()
app.include_router(router, prefix="/reports")
client = TestClient(app)

def test_report_formatter_all_formats(tmp_path):
    formatter = ReportFormatter(artifact_dir=str(tmp_path))
    
    data = {
        "executive_summary": "The model is great.",
        "business_insights": ["Insight 1", "Insight 2"],
        "recommendations": ["Do this", "Do that"],
        "risk_analysis": ["Watch out for bias"],
        "next_steps": ["Deploy"]
    }
    
    md_path = formatter.generate_markdown("test_all", data)
    pdf_path = formatter.generate_pdf(md_path)
    html_path = formatter.generate_html(md_path)
    docx_path = formatter.generate_docx(md_path)
    
    assert os.path.exists(md_path)
    assert os.path.exists(pdf_path)
    assert os.path.exists(html_path)
    assert os.path.exists(docx_path)

@pytest.mark.asyncio
@patch("agents.report_generation_agent.ChatOpenAI")
async def test_report_agent(mock_chat_openai):
    mock_report = ReportData(
        executive_summary="Sum",
        dataset_overview="Data",
        eda_summary="EDA",
        feature_engineering="FE",
        model_comparison="Comp",
        evaluation_metrics="Met",
        explainability="Exp",
        business_insights=["B"],
        recommendations=["R"],
        appendix="App"
    )
    
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_report)
    mock_structured.ainvoke = AsyncMock(return_value=mock_report)
    mock_structured.invoke = MagicMock(return_value=mock_report)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    agent = ReportGenerationAgent()
    mock_state = GraphState(session_id="test")
    
    result = await agent.ainvoke(mock_state, '{"some": "context"}')
    
    assert result["agent_name"] == "report_generation_agent"
    assert "dataset_overview" in result["output"]

def test_download_endpoint(tmp_path):
    # Mock the artifact dir to our tmp path for the test
    import api.v1.endpoints.reports as reports_api
    reports_api.ARTIFACT_DIR = str(tmp_path)
    
    # Create a dummy md file
    test_file = str(tmp_path / "report_test-session.md")
    with open(test_file, "w") as f:
        f.write("# Dummy")
        
    response = client.get("/reports/test-session/download?format=md")
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/markdown; charset=utf-8"
    
    # Test 404
    response = client.get("/reports/bad-session/download?format=md")
    assert response.status_code == 404
    
    # Test bad format
    response = client.get("/reports/test-session/download?format=csv")
    assert response.status_code == 400
