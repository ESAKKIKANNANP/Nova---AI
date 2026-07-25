# =============================================================================
# backend/tests/test_business_insight_agent.py
#
# Unit tests for the Business Insight Agent and Formatter.
# =============================================================================

import pytest
import os
from unittest.mock import AsyncMock, patch
from tools.report_formatter import ReportFormatter
from agents.business_insight_agent import BusinessInsightAgent, BusinessInsightReport
from graphs.state import GraphState

def test_report_formatter_markdown(tmp_path):
    formatter = ReportFormatter(artifact_dir=str(tmp_path))
    
    data = {
        "executive_summary": "The model is great.",
        "business_insights": ["Insight 1", "Insight 2"],
        "recommendations": ["Do this", "Do that"],
        "risk_analysis": ["Watch out for bias"],
        "next_steps": ["Deploy"]
    }
    
    md_path = formatter.generate_markdown("test", data)
    assert os.path.exists(md_path)
    
    with open(md_path, "r") as f:
        content = f.read()
        assert "## Executive Summary" in content
        assert "The model is great." in content
        assert "- Insight 1" in content

def test_report_formatter_pdf(tmp_path):
    formatter = ReportFormatter(artifact_dir=str(tmp_path))
    
    data = {
        "executive_summary": "The model is great.",
    }
    
    md_path = formatter.generate_markdown("test_pdf", data)
    pdf_path = formatter.generate_pdf(md_path)
    
    # fpdf2 should successfully create the file
    assert pdf_path is not None
    assert os.path.exists(pdf_path)

@pytest.mark.asyncio
@patch("agents.business_insight_agent.ChatOpenAI")
async def test_business_insight_agent(mock_chat_openai):
    mock_report = BusinessInsightReport(
        executive_summary="Summary",
        business_insights=["B1"],
        recommendations=["R1"],
        risk_analysis=["Risk1"],
        next_steps=["N1"]
    )
    
    from unittest.mock import MagicMock
    mock_llm_instance = MagicMock()
    mock_structured = AsyncMock(return_value=mock_report)
    mock_structured.ainvoke = AsyncMock(return_value=mock_report)
    mock_structured.invoke = MagicMock(return_value=mock_report)
    mock_llm_instance.with_structured_output.return_value = mock_structured
    mock_chat_openai.return_value = mock_llm_instance
    
    agent = BusinessInsightAgent()
    mock_state = GraphState(session_id="test")
    
    result = await agent.ainvoke(mock_state, "EDA", {"acc": 0.9}, "SHAP")
    
    assert result["agent_name"] == "business_insight_agent"
    assert "executive_summary" in result["output"]
    assert "recommendations" in result["output"]
