# =============================================================================
# backend/tools/visualization/chart_renderer.py
#
# Visualization Tool: Generates plots (matplotlib base64 / Plotly JSON) for analysis.
# =============================================================================

import base64
import io
from typing import Any, Dict, List, Optional
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless environments
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from tools.base import BaseTool


class ChartRendererInput(BaseModel):
    data: List[Dict[str, Any]] = Field(
        ...,
        description="The dataset records (list of dictionaries) containing keys to plot.",
    )
    chart_type: str = Field(
        ...,
        description="Type of chart (e.g. line, scatter, bar, box, histogram, correlation_heatmap).",
    )
    x_column: Optional[str] = Field(
        default=None,
        description="Column name for the X axis.",
    )
    y_column: Optional[str] = Field(
        default=None,
        description="Column name for the Y axis.",
    )
    hue_column: Optional[str] = Field(
        default=None,
        description="Optional column name for grouping/coloring lines or points.",
    )
    title: Optional[str] = Field(
        default=None,
        description="Main title of the plot.",
    )
    xlabel: Optional[str] = Field(
        default=None,
        description="Label for the X axis.",
    )
    ylabel: Optional[str] = Field(
        default=None,
        description="Label for the Y axis.",
    )


class ChartRendererTool(BaseTool):
    """
    Tool that generates plots and outputs them as Base64-encoded PNG strings.
    Also produces metadata suitable for rendering interactive Plotly charts.
    """
    name = "chart_renderer"
    description = "Renders visualizations (line, bar, scatter, box, histogram, heatmaps) from records. Returns a base64-encoded PNG image."
    args_schema = ChartRendererInput

    def _run(
        self,
        data: List[Dict[str, Any]],
        chart_type: str,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
        hue_column: Optional[str] = None,
        title: Optional[str] = None,
        xlabel: Optional[str] = None,
        ylabel: Optional[str] = None,
    ) -> Dict[str, Any]:
        # 1. Validation & Dataframe Conversion
        if not data:
            raise ValueError("Data records list cannot be empty.")
        
        df = pd.DataFrame(data)
        chart_type = chart_type.lower()
        
        plt.figure(figsize=(10, 6))
        
        # 2. Rendering Logic based on chart type
        if chart_type == "line":
            if not x_column or not y_column:
                raise ValueError("Line charts require both x_column and y_column parameters.")
            if hue_column and hue_column in df.columns:
                for label, group in df.groupby(hue_column):
                    plt.plot(group[x_column], group[y_column], label=str(label), marker="o")
                plt.legend()
            else:
                plt.plot(df[x_column], df[y_column], marker="o")

        elif chart_type == "scatter":
            if not x_column or not y_column:
                raise ValueError("Scatter plots require both x_column and y_column parameters.")
            if hue_column and hue_column in df.columns:
                for label, group in df.groupby(hue_column):
                    plt.scatter(group[x_column], group[y_column], label=str(label), alpha=0.8)
                plt.legend()
            else:
                plt.scatter(df[x_column], df[y_column], alpha=0.8)

        elif chart_type == "bar":
            if not x_column or not y_column:
                raise ValueError("Bar charts require both x_column and y_column parameters.")
            
            # Simple bar plot
            if hue_column and hue_column in df.columns:
                # Pivoted table for grouped bars
                pivoted = df.pivot(index=x_column, columns=hue_column, values=y_column)
                pivoted.plot(kind="bar", ax=plt.gca())
            else:
                plt.bar(df[x_column].astype(str), df[y_column])
                plt.xticks(rotation=45)

        elif chart_type == "box":
            if not y_column:
                raise ValueError("Box plots require a target y_column parameter.")
            if x_column and x_column in df.columns:
                # Grouped box plots
                groups = [group[y_column].dropna().values for _, group in df.groupby(x_column)]
                labels = [str(name) for name, _ in df.groupby(x_column)]
                plt.boxplot(groups, tick_labels=labels)
            else:
                plt.boxplot(df[y_column].dropna().values)

        elif chart_type == "histogram":
            if not x_column:
                raise ValueError("Histograms require an target x_column parameter.")
            plt.hist(df[x_column].dropna(), bins="auto", alpha=0.75, edgecolor="black")

        elif chart_type == "correlation_heatmap":
            # Filter to numeric columns only
            numeric_df = df.select_dtypes(include=[np.number])
            if numeric_df.empty:
                raise ValueError("Correlation heatmaps require at least one numeric column in the dataset.")
            corr = numeric_df.corr()
            
            # Plot correlation heatmap
            im = plt.imshow(corr, cmap="coolwarm", interpolation="nearest", vmin=-1, vmax=1)
            plt.colorbar(im)
            plt.xticks(range(len(corr.columns)), corr.columns, rotation=90)
            plt.yticks(range(len(corr.columns)), corr.columns)
            
            # Write numbers inside cell matrices
            for i in range(len(corr.columns)):
                for j in range(len(corr.columns)):
                    plt.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", color="black")
        else:
            raise ValueError(
                f"Unsupported chart_type: {chart_type}. Choose from line, scatter, bar, box, histogram, correlation_heatmap."
            )

        # Style & Details
        plt.title(title or f"{chart_type.title()} Plot")
        plt.xlabel(xlabel or x_column or "")
        plt.ylabel(ylabel or y_column or "")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        # Save to buffer as base64
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        plt.close()
        buf.seek(0)
        base64_str = base64.b64encode(buf.read()).decode("utf-8")

        # Returns base64 image string and basic configuration metadata
        return {
            "chart_type": chart_type,
            "image_base64": f"data:image/png;base64,{base64_str}",
            "plotly_spec": {
                "chart_type": chart_type,
                "x": x_column,
                "y": y_column,
                "hue": hue_column
            }
        }
