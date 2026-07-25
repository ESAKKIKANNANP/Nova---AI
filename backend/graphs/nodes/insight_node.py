# =============================================================================
# backend/graphs/nodes/insight_node.py
#
# LangGraph node for synthesizing all prior outputs into a master business report.
# =============================================================================

import logging
from graphs.state import GraphState
from tools.report_formatter import ReportFormatter
from agents.business_insight_agent import BusinessInsightAgent

log = logging.getLogger(__name__)

async def insight_node(state: GraphState) -> GraphState:
    log.info(f"Executing insight_node for session: {state.get('session_id')}")
    
    # 1. Gather Context
    eda_summary = "EDA Summary Placeholder" # In a real app, pull from EDA agent output
    eda_results = state.get("execution_results", {}).get("eda_node", {})
    if eda_results:
        eda_summary = str(eda_results)
        
    eval_results = state.get("execution_results", {}).get("eval_node", {})
    raw_metrics = eval_results.get("raw_metrics", {})
    
    explain_results = state.get("execution_results", {}).get("explain_node", {}).get("business_summary", {})
    explain_summary = explain_results.get("executive_summary", "No explainability summary found.")
    
    # 2. Invoke Business Insight Agent
    agent = BusinessInsightAgent()
    try:
        agent_output = await agent.ainvoke(state, eda_summary, raw_metrics, explain_summary)
    except Exception as e:
        log.error(f"Business Insight agent failed: {e}")
        return {"current_node": "insight_node", "error_message": f"Insight agent failed: {str(e)}"}
        
    insight_data = agent_output["output"]
    
    # 3. Format into Markdown and PDF
    formatter = ReportFormatter()
    
    # Gather plot paths from previous nodes
    plot_paths = []
    for art in state.get("artifacts", []):
        if art.get("artifact_type") == "image":
            plot_paths.append(art.get("s3_path"))
            
    md_path = formatter.generate_markdown(state.get("session_id", "default"), insight_data, plot_paths)
    pdf_path = formatter.generate_pdf(md_path)
    
    # 4. Save Artifacts
    new_artifacts = [
        {
            "artifact_id": f"final-report-md-{state.get('session_id')}",
            "artifact_type": "report_md",
            "s3_path": md_path,
            "mime_type": "text/markdown",
            "title": "Master Business Report (Markdown)"
        }
    ]
    
    if pdf_path:
        new_artifacts.append({
            "artifact_id": f"final-report-pdf-{state.get('session_id')}",
            "artifact_type": "report_pdf",
            "s3_path": pdf_path,
            "mime_type": "application/pdf",
            "title": "Master Business Report (PDF)"
        })
        
    return {
        "current_node": "insight_node",
        "artifacts": new_artifacts,
        "agent_outputs": [agent_output],
        "execution_results": {"insight_node": {"insight_data": insight_data}},
        "is_complete": True # Signal that the entire pipeline is done
    }
