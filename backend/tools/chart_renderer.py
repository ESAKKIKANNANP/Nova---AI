# =============================================================================
# tools/chart_renderer.py
#
# Tool for generating interactive Plotly charts safely.
# =============================================================================

import os
import uuid
import logging
from typing import Dict, Any, List

log = logging.getLogger(__name__)

# Ensure artifacts directory exists
ARTIFACTS_DIR = "artifacts"
os.makedirs(ARTIFACTS_DIR, exist_ok=True)

def generate_eda_plots(dataset_path: str, plot_requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates Plotly interactive HTML charts based on LLM requests.
    Saves the charts to the filesystem and returns a summary of the plotted data
    so the LLM can interpret the results without seeing the actual image.
    
    Args:
        dataset_path: Path to the raw CSV/Parquet file.
        plot_requests: List of dicts e.g. [{"plot_type": "histogram", "columns": ["age"]}]
        
    Returns:
        List of dicts containing the saved artifact path and a text summary of the data.
    """
    import pandas as pd
    import plotly.express as px
    import plotly.graph_objects as go
    
    log.info(f"Generating {len(plot_requests)} plots for dataset: {dataset_path}")
    
    ext = os.path.splitext(dataset_path)[1].lower()
    if ext == ".csv":
        df = pd.read_csv(dataset_path)
    elif ext == ".parquet":
        df = pd.read_parquet(dataset_path)
    else:
        df = pd.read_csv(dataset_path) # Fallback attempt
        
    results = []
    
    for req in plot_requests:
        plot_type = req.get("plot_type")
        columns = req.get("columns", [])
        
        try:
            fig = None
            summary = ""
            file_id = str(uuid.uuid4())
            filename = f"{plot_type}_{file_id}.html"
            filepath = os.path.join(ARTIFACTS_DIR, filename)
            
            if plot_type == "histogram" and len(columns) >= 1:
                col = columns[0]
                fig = px.histogram(df, x=col, title=f"Distribution of {col}")
                stats = df[col].describe().to_dict()
                summary = f"Histogram of {col}. Mean: {stats.get('mean', 'N/A')}, Min: {stats.get('min', 'N/A')}, Max: {stats.get('max', 'N/A')}."
                
            elif plot_type == "box_plot" and len(columns) >= 1:
                col = columns[0]
                target = columns[1] if len(columns) > 1 else None
                fig = px.box(df, x=target, y=col, title=f"Box Plot of {col}" + (f" by {target}" if target else ""))
                outliers_count = int(df[col].quantile(0.99) < df[col]) # Rough outlier estimate
                summary = f"Box plot of {col}. Upper tail outliers detected: {outliers_count}."
                
            elif plot_type == "scatter_plot" and len(columns) >= 2:
                x, y = columns[0], columns[1]
                fig = px.scatter(df, x=x, y=y, title=f"Scatter Plot: {x} vs {y}")
                corr = df[[x, y]].corr().iloc[0,1]
                summary = f"Scatter plot of {x} vs {y}. Pearson correlation: {corr:.3f}."
                
            elif plot_type == "correlation_matrix":
                numeric_df = df.select_dtypes(include=['number'])
                corr_matrix = numeric_df.corr()
                fig = px.imshow(corr_matrix, text_auto=True, title="Correlation Matrix")
                
                # Find top absolute correlations (excluding self-correlation 1.0)
                correlations = corr_matrix.unstack().sort_values(key=abs, ascending=False).dropna()
                correlations = correlations[correlations < 0.999] # Remove self
                top_corr = correlations.head(4).to_dict()
                summary = f"Correlation matrix. Top correlations: {top_corr}."
                
            elif plot_type == "class_distribution" and len(columns) >= 1:
                col = columns[0]
                counts = df[col].value_counts().reset_index()
                counts.columns = [col, 'count']
                fig = px.bar(counts, x=col, y='count', title=f"Class Distribution of {col}")
                summary = f"Class distribution of {col}. Top classes: {df[col].value_counts().head(3).to_dict()}."
                
            elif plot_type == "missing_value_chart":
                missing = (df.isnull().sum() / len(df)) * 100
                missing = missing[missing > 0].sort_values(ascending=False).reset_index()
                if not missing.empty:
                    missing.columns = ['column', 'missing_percentage']
                    fig = px.bar(missing, x='column', y='missing_percentage', title="Missing Values (%)")
                    summary = f"Missing values present in: {missing.to_dict('records')}."
                else:
                    summary = "No missing values found in the dataset."
            
            if fig:
                # Save as interactive HTML
                fig.write_html(filepath, include_plotlyjs='cdn')
                results.append({
                    "plot_type": plot_type,
                    "columns": columns,
                    "artifact_path": filepath,
                    "summary": summary
                })
                
        except Exception as e:
            log.warning(f"Failed to generate plot {plot_type} for columns {columns}: {str(e)}")
            
    return results
