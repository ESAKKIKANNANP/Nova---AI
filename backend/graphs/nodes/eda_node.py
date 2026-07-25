# =============================================================================
# graphs/nodes/eda_node.py
#
# LangGraph node wrapping the EDAAgent.
# =============================================================================

import logging
from graphs.state import GraphState

log = logging.getLogger(__name__)

async def eda_node(state: GraphState) -> GraphState:
    log.info(f"Executing eda_node for session: {state.get('session_id')}")
    
    data_profile = state.get("data_profile", {})
    column_profiles = data_profile.get("column_profiles", {})
    target_col = data_profile.get("target_column")
    
    chart_specs = []
    
    # 1. Identify columns by roles/dtypes
    numeric_cols = []
    categorical_cols = []
    date_cols = []
    
    for col, profile in column_profiles.items():
        role = profile.get("role", "feature")
        dtype = profile.get("dtype", "object")
        cardinality = profile.get("cardinality", 0)
        
        if role == "date" or "datetime" in dtype:
            date_cols.append(col)
        elif "int" in dtype or "float" in dtype:
            numeric_cols.append(col)
        elif cardinality > 0 and cardinality <= 20:
            categorical_cols.append(col)
            
    # 2. Generate Time Series chart if date exists
    if date_cols and numeric_cols:
        date_col = date_cols[0]
        num_col = numeric_cols[0]
        chart_specs.append({
            "chart_type": "line",
            "columns": [date_col, num_col],
            "title": f"Chronological Trend of {num_col} over {date_col}",
            "rationale": f"Analyze patterns, trends, and seasonal variations of {num_col} over time."
        })
        
    # 3. Generate Category breakdown charts
    for col in categorical_cols[:3]: # Limit to top 3 categorical features
        chart_specs.append({
            "chart_type": "donut" if len(chart_specs) % 2 == 0 else "bar",
            "columns": [col],
            "title": f"{col} Class Share & Distribution",
            "rationale": f"Observe category proportions and flag class imbalances in '{col}'."
        })
        
    # 4. Generate Target correlations
    if target_col:
        target_profile = column_profiles.get(target_col, {})
        target_dtype = target_profile.get("dtype", "object")
        
        if "int" in target_dtype or "float" in target_dtype:
            # Numeric Target vs Numeric Features
            for feat in [c for c in numeric_cols if c != target_col][:2]:
                chart_specs.append({
                    "chart_type": "scatter",
                    "columns": [feat, target_col],
                    "title": f"{target_col} correlation with {feat}",
                    "rationale": f"Detect linear or non-linear dependencies between continuous variables."
                })
        else:
            # Categorical Target vs Numeric Features
            for feat in [c for c in numeric_cols if c != target_col][:2]:
                chart_specs.append({
                    "chart_type": "bar",
                    "columns": [target_col, feat],
                    "title": f"Average {feat} across {target_col} classes",
                    "rationale": f"Identify feature variance across categorical target bins."
                })
                
    # 5. Fallback if no specs generated
    if not chart_specs and len(numeric_cols) >= 2:
        chart_specs.append({
            "chart_type": "scatter",
            "columns": [numeric_cols[0], numeric_cols[1]],
            "title": f"Relationship: {numeric_cols[0]} vs {numeric_cols[1]}",
            "rationale": "Identify baseline correlation between primary numerical columns."
        })
        
    if not chart_specs:
        # Default fallback table spec
        chart_specs.append({
            "chart_type": "table",
            "columns": list(column_profiles.keys())[:5],
            "title": "Dataset Snapshot",
            "rationale": "Tabular preview of primary columns in the dataset."
        })
        
    log.info(f"Generated {len(chart_specs)} chart specifications dynamically.")
    
    # 6. Apply Agent 7 layout bin-packing
    widgets = []
    position = 0
    business_context = state.get("business_context") or {}
    key_metrics = business_context.get("key_metrics", ["Sales", "Profit", "Quantity"])
    
    kpi_span = max(3, 12 // max(1, len(key_metrics)))
    for kpi in key_metrics:
        widgets.append({
            "widget_type": "kpi",
            "data_binding_key": kpi,
            "grid_position": position,
            "size": kpi_span
        })
        position += 1
        
    for spec in chart_specs:
        chart_type = spec.get("chart_type", "bar")
        span = 12 if chart_type == "line" else 6
        widgets.append({
            "widget_type": "chart",
            "data_binding_key": spec.get("title", ""),
            "grid_position": position,
            "size": span
        })
        position += 1
        
    return {
        "current_node": "eda_node",
        "chart_specs": chart_specs,
        "widgets": widgets,
        "execution_results": {
            "eda_node": {
                "generated_plots": len(chart_specs),
                "chart_specs": chart_specs,
                "widgets": widgets
            }
        }
    }
