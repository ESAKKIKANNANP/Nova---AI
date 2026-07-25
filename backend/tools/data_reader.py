# =============================================================================
# tools/data_reader.py
#
# Tool for reading datasets and extracting raw pandas statistics safely.
# =============================================================================

import os
import logging
from typing import Dict, Any

log = logging.getLogger(__name__)

def extract_raw_stats(dataset_path: str) -> Dict[str, Any]:
    """
    Safely reads a dataset (CSV, Parquet, Excel) and computes raw statistical
    summaries to feed into the Analyzer Agent's prompt.
    
    This is executed safely within the backend context, preventing the LLM 
    from needing to write and execute arbitrary pandas code just to get basic info.
    """
    import pandas as pd
    
    log.info(f"Extracting raw stats for dataset: {dataset_path}")
    
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found at path: {dataset_path}")
        
    ext = os.path.splitext(dataset_path)[1].lower()
    
    try:
        if ext == ".csv":
            df = pd.read_csv(dataset_path)
        elif ext == ".parquet":
            df = pd.read_parquet(dataset_path)
        elif ext in [".xls", ".xlsx"]:
            df = pd.read_excel(dataset_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")
            
        # Compute raw stats
        stats = {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": df.columns.tolist(),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "missing_values": df.isnull().sum().to_dict(),
            "missing_pct": (df.isnull().sum() / len(df) * 100).to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": float(df.memory_usage(deep=True).sum() / (1024 * 1024)),
            "numeric_columns": df.select_dtypes(include=['number']).columns.tolist(),
            "categorical_columns": df.select_dtypes(include=['object', 'category', 'bool']).columns.tolist(),
            "datetime_columns": df.select_dtypes(include=['datetime']).columns.tolist(),
            "numeric_summary": df.describe().to_dict(),
            "cardinalities": {col: int(df[col].nunique()) for col in df.columns},
            "sample_values": {col: [str(x) for x in df[col].dropna().head(5).tolist()] for col in df.columns},
            # For categorical, get unique counts and top value
            "categorical_summary": {}
        }
        
        for col in stats["categorical_columns"]:
            stats["categorical_summary"][col] = {
                "unique_count": int(df[col].nunique()),
                "top_value": str(df[col].mode()[0]) if not df[col].mode().empty else None,
                "value_counts": df[col].value_counts(normalize=True).head(5).to_dict() # Top 5 class distribution
            }
            
        log.info(f"Successfully extracted stats. Shape: {stats['rows']}x{stats['columns']}")
        return stats
        
    except Exception as e:
        log.error(f"Error reading dataset stats: {str(e)}")
        raise
