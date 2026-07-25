import pandas as pd
import numpy as np
import os

def generate_customer_churn_dataset(output_path: str):
    """Generates a synthetic customer churn dataset with realistic ML challenges."""
    np.random.seed(42)
    n_rows = 1000
    
    data = {
        'customer_id': [f"CUST_{i}" for i in range(n_rows)],
        'age': np.random.normal(45, 15, n_rows).astype(int),
        'monthly_charges': np.random.uniform(20.0, 120.0, n_rows),
        'total_spent': np.random.uniform(200.0, 5000.0, n_rows),
        'contract_type': np.random.choice(['Month-to-month', 'One year', 'Two year'], n_rows),
        'internet_service': np.random.choice(['DSL', 'Fiber optic', 'No'], n_rows),
        'churn': np.random.choice(['Yes', 'No'], n_rows, p=[0.25, 0.75])
    }
    
    df = pd.DataFrame(data)
    
    # Introduce some missing values to test Data Cleaning agent
    missing_indices = np.random.choice(df.index, size=50, replace=False)
    df.loc[missing_indices, 'monthly_charges'] = np.nan
    
    missing_indices_age = np.random.choice(df.index, size=30, replace=False)
    df.loc[missing_indices_age, 'age'] = np.nan
    
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated synthetic dataset at {output_path} with {n_rows} rows.")

if __name__ == "__main__":
    csv_dir = os.path.dirname(os.path.abspath(__file__))
    generate_customer_churn_dataset(os.path.join(csv_dir, "customer_churn.csv"))
