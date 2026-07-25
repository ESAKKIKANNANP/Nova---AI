# =============================================================================
# backend/tools/model_explainer.py
#
# Deterministic Python tool that calculates SHAP and permutation importance,
# and generates visualization plots for ML models.
# =============================================================================

import os
import joblib
import logging
import pandas as pd
import numpy as np

# Use Agg backend for matplotlib so it doesn't try to open GUI windows
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns

import shap
from sklearn.inspection import permutation_importance, PartialDependenceDisplay

log = logging.getLogger(__name__)

class ModelExplainer:
    def __init__(self, artifact_dir: str = "artifacts/models"):
        self.artifact_dir = artifact_dir

    def generate_explanations(self, model_name: str, problem_type: str) -> dict:
        """
        Loads the specified model and X_test, computes feature importances, 
        generates SHAP plots, and returns a dictionary of the top features.
        """
        x_test_path = os.path.join(self.artifact_dir, "X_test.joblib")
        y_test_path = os.path.join(self.artifact_dir, "y_test.joblib")
        model_path = os.path.join(self.artifact_dir, f"{model_name}_optimized.joblib")
        
        # Fallback to the non-optimized model if optuna was skipped
        if not os.path.exists(model_path):
            model_path = os.path.join(self.artifact_dir, f"{model_name}_best.joblib")
            
        if not os.path.exists(x_test_path) or not os.path.exists(model_path):
            raise FileNotFoundError("Model or test data missing. Ensure prior agents succeeded.")
            
        X_test: pd.DataFrame = joblib.load(x_test_path)
        y_test = joblib.load(y_test_path)
        model = joblib.load(model_path)
        
        # Subsample to 500 rows for speed
        if len(X_test) > 500:
            np.random.seed(42)
            idx = np.random.choice(X_test.index, 500, replace=False)
            X_sample = X_test.loc[idx]
            y_sample = y_test.loc[idx] if isinstance(y_test, pd.Series) else y_test[idx]
        else:
            X_sample = X_test
            y_sample = y_test
            
        is_tree = any(name in model_name for name in ["RandomForest", "XGB", "LGBM"])
        
        feature_importance_dict = {}
        plots = []
        
        # 1. Feature Importance (SHAP or Permutation)
        try:
            plt.figure(figsize=(10, 6))
            if is_tree:
                # Use TreeExplainer
                explainer = shap.TreeExplainer(model)
                shap_values = explainer.shap_values(X_sample)
                
                # shap_values might be a list for multi-class. Extract the first or combined
                vals = shap_values[1] if isinstance(shap_values, list) else shap_values
                
                shap.summary_plot(vals, X_sample, show=False)
                plot_path = os.path.join(self.artifact_dir, "shap_summary.png")
                plt.savefig(plot_path, bbox_inches='tight')
                plots.append(plot_path)
                
                # Aggregate to get top features
                mean_abs_shap = np.abs(vals).mean(axis=0)
                if len(mean_abs_shap.shape) > 1:
                    mean_abs_shap = mean_abs_shap.mean(axis=1) # Flatten multi-class
                    
                for i, col in enumerate(X_sample.columns):
                    feature_importance_dict[col] = float(mean_abs_shap[i])
                    
            else:
                # Use Permutation Importance for non-tree models
                result = permutation_importance(model, X_sample, y_sample, n_repeats=5, random_state=42, n_jobs=-1)
                for i, col in enumerate(X_sample.columns):
                    feature_importance_dict[col] = float(result.importances_mean[i])
                    
                # Basic bar plot
                sorted_idx = result.importances_mean.argsort()[-10:] # Top 10
                plt.barh(np.array(X_sample.columns)[sorted_idx], result.importances_mean[sorted_idx])
                plt.xlabel("Permutation Importance")
                plt.title("Top 10 Feature Importances")
                plot_path = os.path.join(self.artifact_dir, "permutation_importance.png")
                plt.savefig(plot_path, bbox_inches='tight')
                plots.append(plot_path)
                
        except Exception as e:
            log.warning(f"Failed to generate SHAP/Permutation plot: {e}")
        finally:
            plt.close()
            
        # 2. PDP for Top 2 features
        try:
            sorted_feats = sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True)
            top_2 = [f[0] for f in sorted_feats[:2]]
            
            if top_2:
                fig, ax = plt.subplots(figsize=(12, 5))
                PartialDependenceDisplay.from_estimator(model, X_sample, top_2, ax=ax)
                plot_path = os.path.join(self.artifact_dir, "pdp_top_features.png")
                plt.savefig(plot_path, bbox_inches='tight')
                plots.append(plot_path)
                plt.close(fig)
        except Exception as e:
            log.warning(f"Failed to generate PDP plots: {e}")

        # Sort dict
        feature_importance_dict = dict(sorted(feature_importance_dict.items(), key=lambda x: x[1], reverse=True))

        return {
            "feature_importance": feature_importance_dict,
            "plots": plots
        }
