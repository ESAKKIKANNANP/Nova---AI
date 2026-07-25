# =============================================================================
# backend/graphs/nodes/report_node.py
#
# LangGraph node for synthesizing the final massive report into 4 formats.
# =============================================================================

import os
import logging
import json
from graphs.state import GraphState
from tools.report_formatter import ReportFormatter
from agents.report_generation_agent import ReportGenerationAgent

log = logging.getLogger(__name__)

async def report_node(state: GraphState) -> GraphState:
    log.info(f"Executing report_node for session: {state.get('session_id')}")
    
    # 1. Gather Massive Context
    # We serialize all execution results into a string block
    pipeline_context = json.dumps(state.get("execution_results", {}), indent=2, default=str)
    
    # 2. Invoke Report Agent
    agent = ReportGenerationAgent()
    try:
        agent_output = await agent.ainvoke(state, pipeline_context)
    except Exception as e:
        log.error(f"Report agent failed: {e}")
        return {"current_node": "report_node", "error_message": f"Report agent failed: {str(e)}"}
        
    report_data = agent_output["output"]
    
    # 3. Format into Markdown, HTML, DOCX, and PDF
    formatter = ReportFormatter()
    
    # Gather plot paths
    plot_paths = []
    for art in state.get("artifacts", []):
        if art.get("artifact_type") == "image":
            plot_paths.append(art.get("s3_path"))
            
    # We can reuse the markdown generator by mapping the new schema to it, or writing a custom one.
    # To save space, we just inject the massive new schema into the existing markdown generator 
    # by merging the fields so it looks like the old schema but bigger.
    merged_data = {
        "executive_summary": f"**Executive Summary:**\n{report_data.get('executive_summary')}\n\n"
                             f"**Dataset Overview:**\n{report_data.get('dataset_overview')}\n\n"
                             f"**EDA Summary:**\n{report_data.get('eda_summary')}\n\n"
                             f"**Feature Engineering:**\n{report_data.get('feature_engineering')}\n\n"
                             f"**Model Comparison:**\n{report_data.get('model_comparison')}\n\n"
                             f"**Evaluation Metrics:**\n{report_data.get('evaluation_metrics')}\n\n"
                             f"**Explainability:**\n{report_data.get('explainability')}\n\n"
                             f"**Appendix:**\n{report_data.get('appendix')}",
        "business_insights": report_data.get("business_insights", []),
        "recommendations": report_data.get("recommendations", []),
        "risk_analysis": ["See Appendix for technical risks"],
        "next_steps": ["Deploy model"]
    }
            
    md_path = formatter.generate_markdown(state.get("session_id", "default"), merged_data, plot_paths)
    pdf_path = formatter.generate_pdf(md_path)
    html_path = formatter.generate_html(md_path)
    docx_path = formatter.generate_docx(md_path)
    
    # 4. Save Artifacts
    new_artifacts = [
        {
            "artifact_id": f"final-report-md-{state.get('session_id')}",
            "artifact_type": "report_md",
            "s3_path": md_path,
            "mime_type": "text/markdown",
            "title": "Master Report (Markdown)"
        },
        {
            "artifact_id": f"final-report-html-{state.get('session_id')}",
            "artifact_type": "report_html",
            "s3_path": html_path,
            "mime_type": "text/html",
            "title": "Master Report (HTML)"
        },
        {
            "artifact_id": f"final-report-docx-{state.get('session_id')}",
            "artifact_type": "report_docx",
            "s3_path": docx_path,
            "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "title": "Master Report (DOCX)"
        }
    ]
    
    if pdf_path:
        new_artifacts.append({
            "artifact_id": f"final-report-pdf-{state.get('session_id')}",
            "artifact_type": "report_pdf",
            "s3_path": pdf_path,
            "mime_type": "application/pdf",
            "title": "Master Report (PDF)"
        })
        
    return {
        "current_node": "report_node",
        "artifacts": new_artifacts,
        "agent_outputs": [agent_output],
        "execution_results": {"report_node": {"report_data": report_data}},
        "is_complete": True 
    }
