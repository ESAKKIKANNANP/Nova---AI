# =============================================================================
# backend/tools/data/csv_loader.py
#
# CSV and Excel File Tool: Ingests, profiles, and validates data files.
# Generates column statistics, schema metadata, and data previews.
# =============================================================================

import os
import pandas as pd
from typing import Any, Dict, Optional, List
from pydantic import BaseModel, Field

from tools.base import BaseTool


class FileLoaderInput(BaseModel):
    file_path: str = Field(
        ...,
        description="Absolute file path to the CSV or Excel file.",
    )
    delimiter: str = Field(
        default=",",
        description="Delimiter character for CSV files (ignored for Excel).",
    )
    sheet_name: Optional[str] = Field(
        default=None,
        description="Sheet name to load for Excel files (optional).",
    )
    nrows: Optional[int] = Field(
        default=None,
        description="Maximum number of rows to parse for analysis and preview.",
    )


class FileLoaderTool(BaseTool):
    """
    Tool that ingests CSV or Excel data files, performs validation,
    extracts structural schemas, profiles statistics, and generates previews.
    """
    name = "file_loader"
    description = "Ingests and profiles CSV/Excel data files, extracting schema details, shape, summary statistics, and preview rows."
    args_schema = FileLoaderInput

    def _run(self, file_path: str, delimiter: str = ",", sheet_name: Optional[str] = None, nrows: Optional[int] = None) -> Dict[str, Any]:
        # 1. Existence Validation
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Data file not found at path: {file_path}")

        # Determine file type
        _, ext = os.path.splitext(file_path.lower())
        
        # 2. Ingest file into pandas DataFrame
        try:
            if ext in (".xls", ".xlsx"):
                sheet_to_use = sheet_name if sheet_name is not None else 0
                df = pd.read_excel(file_path, sheet_name=sheet_to_use, nrows=nrows)
            elif ext in (".csv", ".txt"):
                df = pd.read_csv(file_path, sep=delimiter, nrows=nrows)
            elif ext == ".parquet":
                df = pd.read_parquet(file_path)
                if nrows is not None:
                    df = df.head(nrows)
            else:
                raise ValueError(f"Unsupported file format: {ext}. Allowed types: .csv, .xlsx, .xls, .parquet, .txt")
        except Exception as exc:
            raise RuntimeError(f"Error parsing data file: {exc}")

        # 3. Compute Schema Metadata
        row_count, col_count = df.shape
        columns_summary: List[Dict[str, Any]] = []

        for col in df.columns:
            series = df[col]
            missing_count = int(series.isnull().sum())
            missing_ratio = float(missing_count / row_count) if row_count > 0 else 0.0
            
            col_info = {
                "name": str(col),
                "data_type": str(series.dtype),
                "missing_count": missing_count,
                "missing_ratio": round(missing_ratio, 4),
                "cardinality": int(series.nunique())
            }
            
            # Numeric column specific stats
            if pd.api.types.is_numeric_dtype(series):
                col_info["mean"] = float(series.mean()) if not series.empty else None
                col_info["std"] = float(series.std()) if not series.empty else None
                col_info["min"] = float(series.min()) if not series.empty else None
                col_info["max"] = float(series.max()) if not series.empty else None
            
            columns_summary.append(col_info)

        # 4. Generate JSON Data Preview
        preview_data = df.head(5).to_dict(orient="records")

        return {
            "file_name": os.path.basename(file_path),
            "file_size_bytes": os.path.getsize(file_path),
            "row_count": row_count,
            "column_count": col_count,
            "columns": columns_summary,
            "preview_data": preview_data
        }
