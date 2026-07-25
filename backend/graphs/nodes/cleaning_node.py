# =============================================================================
# graphs/nodes/cleaning_node.py
#
# Stub node for Data Cleaning.
# =============================================================================

import logging
import os
import pandas as pd
from graphs.state import GraphState

log = logging.getLogger(__name__)

async def cleaning_node(state: GraphState) -> GraphState:
    log.info(f"Executing cleaning_node for session: {state.get('session_id')}")
    
    dataset_path = state.get("dataset_path")
    if not dataset_path or not os.path.exists(dataset_path):
        return {
            "current_node": "cleaning_node",
            "error_message": "Dataset not found for cleaning."
        }
        
    try:
        # Load dataset
        df = pd.read_csv(dataset_path)
        data_profile = state.get("data_profile", {})
        column_profiles = data_profile.get("column_profiles", {})
        
        cleaning_history = []
        columns_to_drop = []
        
        # 1. Clean missing values dynamically per column
        for col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                null_pct = (null_count / len(df)) * 100
                if null_pct > 50.0:
                    columns_to_drop.append(col)
                    cleaning_history.append(f"Dropped column '{col}' due to excessive missing values ({null_pct:.1f}%).")
                else:
                    # Imputation based on datatype
                    if pd.api.types.is_numeric_dtype(df[col]):
                        median_val = df[col].median()
                        df[col] = df[col].fillna(median_val)
                        cleaning_history.append(f"Imputed numerical column '{col}' with median: {median_val}.")
                    else:
                        mode_series = df[col].mode()
                        mode_val = mode_series[0] if not mode_series.empty else "Missing"
                        df[col] = df[col].fillna(mode_val)
                        cleaning_history.append(f"Imputed categorical column '{col}' with mode: '{mode_val}'.")
                        
        if columns_to_drop:
            df = df.drop(columns=columns_to_drop)
            
        # 2. Document encoding decisions (actual encoding happens inside feature node / pipeline)
        for col in df.columns:
            if col in column_profiles:
                cardinality = column_profiles[col].get("cardinality", 0)
                role = column_profiles[col].get("role", "feature")
                dtype = column_profiles[col].get("dtype", "object")
                
                if role == "feature" and ("object" in dtype or "category" in dtype):
                    if cardinality <= 10:
                        cleaning_history.append(f"Selected One-Hot Encoding for categorical column '{col}' (cardinality: {cardinality}).")
                    else:
                        cleaning_history.append(f"Selected Target Encoding for high-cardinality column '{col}' (cardinality: {cardinality}).")
                        
        # 3. Save cleaned dataset
        dir_name = os.path.dirname(dataset_path)
        base_name = os.path.basename(dataset_path)
        cleaned_path = os.path.join(dir_name, "cleaned_" + base_name)
        df.to_csv(cleaned_path, index=False)
        log.info(f"Cleaned dataset saved to: {cleaned_path}")
        
        if not cleaning_history:
            cleaning_history.append("Dataset verified: No missing values or dirty data elements found.")
            
        return {
            "current_node": "cleaning_node",
            "dataset_path": cleaned_path,
            "cleaning_history": cleaning_history
        }
        
    except Exception as e:
        log.error(f"Data cleaning failed: {e}")
        return {
            "current_node": "cleaning_node",
            "error_message": f"Cleaning failed: {str(e)}"
        }
