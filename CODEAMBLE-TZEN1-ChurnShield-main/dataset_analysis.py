import pandas as pd
import os

DATASETS = {
    "telecom": "telecom_churn_dataset.csv",
    "ott": "ott_churn_dataset.csv",
    "banking": "BankChurners.csv"
}

def analyze_datasets():
    for name, filename in DATASETS.items():
        print("=" * 60)
        print(f" DOMAIN: {name.upper()}")
        print("=" * 60)
        
        if not os.path.exists(filename):
            print(f"File not found: {filename}")
            continue

        df = pd.read_csv(filename)
        df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

        if name == "banking" and "Attrition_Flag" in df.columns:
            df["Churn"] = df["Attrition_Flag"].apply(lambda x: 1 if str(x).strip() == "Attrited Customer" else 0)

        print(f"Shape: {df.shape[0]} rows, {df.shape[1]} columns")
        print(f"Duplicate Rows: {df.duplicated().sum()}")
        
        print("\n--- Missing Values ---")
        null_counts = df.isnull().sum()
        print(null_counts[null_counts > 0] if null_counts.sum() > 0 else "No missing values found.")
        
        print("\n--- Target (Churn) Distribution ---")
        churn_counts = df['Churn'].value_counts()
        churn_pct = df['Churn'].value_counts(normalize=True) * 100
        for val in churn_counts.index:
            print(f"  Churn = {val}: {churn_counts[val]} ({churn_pct[val]:.2f}%)")
        
        print("\n--- Data Types ---")
        print(df.dtypes)
        
        print("\n--- Numerical Features Summary ---")
        num_cols = df.select_dtypes(include=['int64', 'float64']).columns.drop('Churn', errors='ignore')
        print(df[num_cols].describe().T[['mean', 'std', 'min', '50%', 'max']])
        
        print("\n--- Categorical Features Breakdown ---")
        cat_cols = df.select_dtypes(include=['object']).columns.drop(['Customer ID', 'CLIENTNUM', 'Attrition_Flag'], errors='ignore')
        for col in cat_cols:
            val_counts = df[col].value_counts().to_dict()
            print(f"  {col} ({df[col].nunique()} categories): {val_counts}")
        print("\n")

if __name__ == "__main__":
    analyze_datasets()
